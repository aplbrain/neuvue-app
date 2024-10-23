import time
import json
import glob
import random
import logging
from typing import List
from datetime import datetime, timedelta

from django.conf import settings
from django.apps import apps

import requests
import os
import backoff
import pandas as pd
import numpy as np
from caveclient import CAVEclient
from nglui.statebuilder import (
    ImageLayerConfig,
    SegmentationLayerConfig,
    AnnotationLayerConfig,
    LineMapper,
    PointMapper,
    StateBuilder,
    ChainedStateBuilder,
)

from .models import (
    Namespace,
    NeuroglancerLinkType,
    PcgChoices,
    ImageChoices,
    NeuroglancerHost,
)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Config = apps.get_model("preferences", "Config")


def get_df_from_static(cave_client, table_name):
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def query_new_table(table_name):
        logging.info(f"Downloading new table for {table_name}.")
        df = cave_client.materialize.query_table(table_name)
        fn = str(round(time.time())) + "_" + table_name + ".pkl"
        df.to_pickle(os.path.join(settings.CACHED_TABLES_PATH, fn))
        return df

    try:
        if not os.path.exists(settings.CACHED_TABLES_PATH):
            os.makedirs(settings.CACHED_TABLES_PATH)

        cached_tables = glob.glob(
            os.path.join(settings.CACHED_TABLES_PATH, "*_" + table_name + ".pkl")
        )
        # filter to table of interest
        if len(cached_tables):
            file_path = cached_tables[0]
            file_name = os.path.split(file_path)[1]
            file_date = int(file_name.split("_")[0])
            if (
                datetime.fromtimestamp(file_date) - datetime.fromtimestamp(time.time())
            ) < timedelta(days=settings.DAYS_UNTIL_EXPIRED):
                logging.info(f"Using cached table for {table_name}.")
                df = pd.read_pickle(file_path)
            else:
                os.remove(file_path)
                df = query_new_table(table_name)
        else:
            df = query_new_table(table_name)
        return df
    except Exception:
        logger.error("Resource table cannot be queried.")
        raise Exception(f"Table {table_name} unavailable.")


def create_base_state(seg_ids, coordinate, namespace=None):
    """Generates a base state containing imagery and segmentation layers.

    Args:
        seg_ids (list): seg_ids to select in the view
        coordinate (tuple|list): collection of three integer voxel coordinates, XYZ order.
        namespace (str): task namespace
    Returns:
        StateBuilder: Base State
    """

    # Create ImageLayerConfig
    if namespace:
        img_source = (
            "precomputed://" + Namespace.objects.get(namespace=namespace).img_source
        )
    else:
        img_source = "precomputed://" + ImageChoices.MINNIE

    try:
        black = settings.DATASET_VIEWER_OPTIONS[img_source]["contrast"]["black"]
        white = settings.DATASET_VIEWER_OPTIONS[img_source]["contrast"]["white"]
    except KeyError:
        black = 0
        white = 1

    img_layer = ImageLayerConfig(
        name="em", source=img_source, contrast_controls=True, black=black, white=white
    )

    # Create SegmentationLayerConfig
    if namespace:
        seg_source = (
            "graphene://" + Namespace.objects.get(namespace=namespace).pcg_source
        )
    else:
        seg_source = "graphene://" + PcgChoices.MINNIE

    segmentation_view_options = {"alpha_selected": 0.6, "alpha_3d": 0.3}
    seg_layer = SegmentationLayerConfig(
        name="seg",
        source=seg_source,
        fixed_ids=seg_ids,
        view_kws=segmentation_view_options,
    )

    view_options = {"position": coordinate, "zoom_image": 20}

    return StateBuilder(layers=[img_layer, seg_layer], view_kws=view_options)


def generate_path_df(points):
    """Generates the point A to point B dataframe for all points. Points are
    assumed to be in sequential order and all part of the same group.

    Args:
        points (Iterable[int[]]): List of points in XYZ order.

    Returns:
        DataFrame: Dataframe of point columns and groups.
    """
    point_column_a = points[:-1].tolist()
    point_column_b = points[1:].tolist()

    group = np.ones(len(point_column_a)).tolist()
    return pd.DataFrame(
        {
            "point_column_a": point_column_a,
            "point_column_b": point_column_b,
            "group": group,
        }
    )


def generate_point_df(points, description=None, group=None):
    """Generates the point A dataframe for all points. Points are
    assumed to be  all part of the same group.

    Args:
        points (Iterable[int[]]): List of points in XYZ order.

    Returns:
        DataFrame: Dataframe of point columns and groups.
    """
    point_column_a = points.tolist()
    if group:
        if len(group) != len(points):
            logger.error("Group array shape does not match points array shape.")
            group = np.ones(len(point_column_a)).tolist()
    else:
        group = np.ones(len(point_column_a)).tolist()

    if description:
        if len(description) != len(points):
            logger.error("Group array shape does not match points array shape.")

        return pd.DataFrame(
            {
                "point_column_a": point_column_a,
                "group": group,
                "description": description,
            }
        )
    else:
        return pd.DataFrame({"point_column_a": point_column_a, "group": group})


def create_path_state():
    """Create the annotation state for paths.

    Returns:
        StateBuilder: Annotation State
    """
    path = AnnotationLayerConfig(
        "selected_paths",
        active=False,
        mapping_rules=LineMapper(
            "point_column_a", "point_column_b", group_column="group"
        ),
    )
    anno = AnnotationLayerConfig("merge_point")
    return StateBuilder(layers=[path, anno], resolution=settings.VOXEL_RESOLUTION)


def create_point_state(name="annotations", group=None, description=None, color=None):
    """Create the annotation state for points.
    Dont use linemapper, just creates a neuroglancer link that is just Points
    nglui statebuilder
    Returns:
        StateBuilder: Annotation State
    """
    anno = AnnotationLayerConfig(
        name,
        mapping_rules=PointMapper(
            "point_column_a",
            group_column=group,
            description_column=description,
            set_position=False,
        ),
        color=color,
    )

    return StateBuilder(layers=[anno], resolution=settings.VOXEL_RESOLUTION)


def construct_proofreading_state(task_df, points, return_as="json"):
    """Generates a Neuroglancer URL with the path/annotation information preloaded.

    Args:
        task_df (pandas.DataFrame): Task Dataframe from Neuvue-Client
        points (List): List of coordinates of the initial set of Point Objects

    Returns:
        string: Neuroglancer URL
    """
    # TODO: Automatically iterate through Namespaces and map them to the
    # appropriate Neuroglancer functions.
    seg_ids = [task_df["seg_id"]]
    base_state = create_base_state(seg_ids, points[0], task_df["namespace"])

    # Get any annotation coordinates. Append original points.
    coordinates = task_df["metadata"].get("coordinates", [])

    # Create a list of dataframes used for state creation. Since first state is
    # the base layer, the first element is None.
    data_list = [None]
    ng_type = Namespace.objects.get(namespace=task_df["namespace"]).ng_link_type
    if ng_type == NeuroglancerLinkType.PATH:

        if points:
            # Append start and end soma coordinates
            coordinates.insert(0, points[0])
            coordinates.append(points[-1])
            coordinates = np.array(coordinates)

        data_list.append(generate_path_df(coordinates))
        path_state = create_path_state()
        chained_state = ChainedStateBuilder([base_state, path_state])

    elif ng_type == NeuroglancerLinkType.POINT:
        # Get grouping and annotation descriptions, if they exist
        coordinates = np.array(coordinates)
        group = task_df["metadata"].get("group")
        description = task_df["metadata"].get("description")
        data_list.append(
            generate_point_df(coordinates, description=description, group=group)
        )
        point_state = create_point_state(bool(description))
        chained_state = ChainedStateBuilder([base_state, point_state])

    elif ng_type == NeuroglancerLinkType.PREGENERATED and task_df.get("ng_state"):
        if return_as == "json":
            return task_df["ng_state"]
        elif return_as == "url":
            return construct_url_from_existing(json.dumps(task_df["ng_state"]))

    return chained_state.render_state(
        data_list, return_as=return_as, url_prefix=settings.NG_CLIENT
    )


def construct_url_from_existing(state: str, ng_host: str):
    if ng_host in [NeuroglancerHost.SPELUNKER, NeuroglancerHost.SPELUNKER_URL]:
        return ng_host + "/#!middleauth+" + state
    else:
        return ng_host + "/#!" + state


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def get_from_state_server(url: str):
    """Gets JSON state string from state server

    Args:
        url (str): json state server link
    Returns:
        (str): JSON String
    """
    url = url.replace("middleauth+", "")
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {os.environ['CAVECLIENT_TOKEN']}",
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception("GET Unsuccessful")

    # TODO: Make sure its JSON String
    return resp.text


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def post_to_state_server(state: str):
    """Posts JSON string to state server

    Args:
        state (str): NG State string

    Returns:
        str: url string
    """
    # Get the authorization token from caveclient
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {os.environ['CAVECLIENT_TOKEN']}",
    }

    # Post!
    resp = requests.post(settings.JSON_STATE_SERVER, data=state, headers=headers)

    if resp.status_code != 200:
        raise Exception("POST Unsuccessful")

    # Response will contain the URL for the state you just posted
    return str(resp.json())


def get_from_json(raw_state: str):
    """Get Neuroglancer state from JSON string

    #TODO: Apply config settings here eventually.

    Args:
        raw state (str): neuroglancer string
    Returns:
        str: validated neuroglancer state
    """
    state_obj = json.loads(raw_state)
    if state_obj.get("value"):
        return json.dumps(state_obj["value"])
    else:
        return raw_state


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def _get_lineage_graph(root_id: str, cave_client):
    """Get a lineage graph with exponential backoff.

    Args:
        root_id (str): segment root id
        cave_client (CAVEClient): caveclient instance

    Raises:
        e: All exceptions

    Returns:
        dict: lineage graph
    """

    try:
        return cave_client.chunkedgraph.get_lineage_graph(
            [root_id],
            timestamp_past=datetime(year=2021, month=11, day=1),
            as_nx_graph=True,
        )
    except Exception as e:
        logging.error(e)
        raise e


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def _get_soma_center(root_ids: List, cave_client):
    """Get the first soma center of a list of root IDs with exponential backoff.

    Args:
        root_id (str): segment root id
        cave_client (CAVEClient): caveclient instance
    Raises:
        e: All exceptions

    Returns:
        array: array for the position of the soma
    """
    try:
        soma_df = cave_client.materialize.query_table(
            settings.NEURON_TABLE, filter_in_dict={"pt_root_id": root_ids[:3]}
        )
        if not len(soma_df):
            soma_df = cave_client.materialize.query_table(
                settings.NEURON_TABLE, filter_in_dict={"pt_root_id": root_ids}
            )
        if len(soma_df) > 3:
            soma_df = soma_df.head(3)
        pt_position = soma_df.iloc[0]["pt_position"]
        present_root_ids = list(soma_df["pt_root_id"])
    except IndexError as e:
        logging.error(e)
        raise Exception("Unable to find Soma Center")
    except Exception as e:
        logging.error(e)
        raise Exception(e)
    return pt_position, present_root_ids


def _get_nx_graph_image(nx_graph):
    def networkx_to_graphViz(nx_graph):
        import graphviz
        import networkx as nx

        gv_graph = graphviz.Digraph(
            "lineage",
            format="svg",
            graph_attr={"size": "6,{}", "ratio": "compress", "ranksep": "0.5"},
            node_attr={"fontsize": "18", "fontname": "Arial"},
        )  # 'size':'6,3',
        timestamps = nx.get_node_attributes(
            nx_graph, "timestamp"
        )  # dictionary of all timestamps in the graph, key: node
        operation_ids = nx.get_node_attributes(
            nx_graph, "operation_id"
        )  # dictionary of all operation ids in the graph, key: node
        for node in nx_graph.nodes():
            label_str = str(node)
            label_str += (
                "\n" + datetime.fromtimestamp(timestamps.get(node)).strftime("%Y-%m-%d")
                if timestamps.get(node)
                else ""
            )  # add timestamp if it exists
            label_str += (
                "\n id: " + str(operation_ids.get(node))
                if operation_ids.get(node)
                else ""
            )  # add operation id if it exists
            gv_graph.node(str(node), label=label_str)
        for edge0, edge1 in nx_graph.edges():
            gv_graph.edge(str(edge0), str(edge1))
        gv_graph = gv_graph.unflatten(stagger=10)
        return gv_graph.pipe(encoding="utf-8")

    return networkx_to_graphViz(nx_graph)


def construct_lineage_state_and_graph(root_id: str):
    """Construct state for the lineage viewer.

    Args:
        root_id (str): segment root id

    Returns:
        string: json-formatted state
    """
    root_id = root_id.strip()
    cave_client = CAVEclient(
        "minnie65_phase3_v1", auth_token=os.environ["CAVECLIENT_TOKEN"]
    )

    # Lineage graph gives you the nodes and edges of a root IDs history
    lineage_graph = _get_lineage_graph(root_id, cave_client)
    graph_image = _get_nx_graph_image(lineage_graph)

    root_ids = {str(x) for x in lineage_graph}

    # Ensure original root ID is in list of shown IDs
    root_ids.add(root_id)
    root_ids = list(root_ids)

    position, root_ids_with_center = _get_soma_center(root_ids, cave_client)
    base_state = create_base_state(root_ids_with_center, position)

    # For the rest of the IDs, we can add them to the seg layer as unselected.
    base_state_dict = base_state.render_state(return_as="dict")
    base_state_dict["layout"] = "3d"
    base_state_dict["selectedLayer"] = {"layer": "seg", "visible": True}
    for layer in base_state_dict["layers"]:
        if layer["name"] == "seg":
            selected_segments = layer["segments"]
            layer["hiddenSegments"] = [
                root_id for root_id in root_ids if root_id not in selected_segments
            ]
    return (
        json.dumps(base_state_dict, default=lambda x: [str(y) for y in x]),
        graph_image,
    )


def apply_state_config(state: str, username: str):
    cdict = json.loads(state)
    cdict["jsonStateServer"] = settings.JSON_STATE_SERVER
    # make ng state preferences changes, json string to dict
    try:
        config = Config.objects.filter(user=username).order_by("-id")[0]
    except Exception as e:
        logging.error(e)
        return json.dumps(cdict)

    if not config.enabled:
        return json.dumps(cdict)

    annotation_color_palette = config.annotation_color_palette
    mesh_color_palette = config.mesh_color_palette
    alpha_selected = config.alpha_selected
    zoom_level = config.zoom_level
    alpha_3d = config.alpha_3d
    gpu_limit = config.gpu_limit
    sys_limit = config.sys_limit
    chunk_requests = config.chunk_requests
    layout = config.layout
    enable_sound = config.enable_sound

    cdict = json.loads(state)

    if config.layout_switch:
        cdict["layout"] = str(layout)
    if config.gpu_limit_switch:
        cdict["gpuMemoryLimit"] = int(float(gpu_limit) * 1e9)
    if config.sys_limit_switch:
        cdict["systemMemoryLimit"] = int(float(sys_limit) * 1e9)
    if config.chunk_requests_switch:
        cdict["concurrentDownloads"] = int(chunk_requests)
    if config.zoom_level_switch:
        cdict["navigation"]["zoomFactor"] = int(zoom_level)
    if config.enable_sound_switch:
        cdict["enableSound"] == enable_sound

    # create color palette dictionary
    annotation_color_palette_dict = {
        "palette1": [
            "#FFADAD",
            "#FFD6A5",
            "#FDFFB6",
            "#CAFFBF",
            "#9BF6FF",
            "#A0C4FF",
            "#BDB2FF",
            "#FFC6FF",
            "#FFFFFC",
        ],
        "palette2": [
            "#F72585",
            "#B5179E",
            "#7209B7",
            "#560BAD",
            "#480CA8",
            "#3A0CA3",
            "#3F37C9",
            "#4361EE",
            "#4895EF",
            "#4CC9F0",
        ],
        "palette3": [
            "#7400B8",
            "#6930C3",
            "#5E60CE",
            "#5390D9",
            "#4EA8DE",
            "#48BFE3",
            "#56CFE1",
            "#64DFDF",
            "#72EFDD",
            "#80FFDB",
        ],
        "palette4": [
            "#F94144",
            "#F3722C",
            "#F8961E",
            "#F9844A",
            "#F9C74F",
            "#90BE6D",
            "#43AA8B",
            "#4D908E",
            "#577590",
            "#277DA1",
        ],
        "palette5": [
            "#005F73",
            "#0A9396",
            "#94D2BD",
            "#E9D8A6",
            "#EE9B00",
            "#CA6702",
            "#BB3E03",
            "#AE2012",
            "#9B2226",
        ],
        "palette6": [
            "#011A51",
            "#1957DB",
            "#487BEA",
            "#7EA3F1",
            "#C8D7F9",
            "#B83700",
            "#F06C00",
            "#FAB129",
            "#FBC55F",
            "#FDE9C3",
        ],
    }

    # create mesh color palette dictionary
    mesh_color_palette_dict = {
        "palette1": [
            "#FFADAD",
            "#FFD6A5",
            "#FDFFB6",
            "#CAFFBF",
            "#9BF6FF",
            "#A0C4FF",
            "#BDB2FF",
            "#FFC6FF",
            "#FFFFFC",
        ],
        "palette2": [
            "#F72585",
            "#B5179E",
            "#7209B7",
            "#560BAD",
            "#480CA8",
            "#3A0CA3",
            "#3F37C9",
            "#4361EE",
            "#4895EF",
            "#4CC9F0",
        ],
        "palette3": [
            "#7400B8",
            "#6930C3",
            "#5E60CE",
            "#5390D9",
            "#4EA8DE",
            "#48BFE3",
            "#56CFE1",
            "#64DFDF",
            "#72EFDD",
            "#80FFDB",
        ],
        "palette4": [
            "#F94144",
            "#F3722C",
            "#F8961E",
            "#F9844A",
            "#F9C74F",
            "#90BE6D",
            "#43AA8B",
            "#4D908E",
            "#577590",
            "#277DA1",
        ],
        "palette5": [
            "#005F73",
            "#0A9396",
            "#94D2BD",
            "#E9D8A6",
            "#EE9B00",
            "#CA6702",
            "#BB3E03",
            "#AE2012",
            "#9B2226",
        ],
        "palette6": [
            "#011A51",
            "#1957DB",
            "#487BEA",
            "#7EA3F1",
            "#C8D7F9",
            "#B83700",
            "#F06C00",
            "#FAB129",
            "#FBC55F",
            "#FDE9C3",
        ],
    }

    # generate random color
    def getRandomHexColor():
        random_number = random.randint(0, 16777215)
        hex_number = str(hex(random_number))
        hex_color = "#" + hex_number[2:].upper()
        return hex_color

    annotation_layer_count = 0
    for layer in cdict["layers"]:
        # handle alpha
        if "segmentation" in layer.get("type", "") and config.alpha_selected_switch:
            layer["selectedAlpha"] = float(alpha_selected)

        if "segmentation" in layer.get("type", "") and config.alpha_3d_switch:
            layer["objectAlpha"] = float(alpha_3d)

        # handle annotation layer colors
        if (
            layer.get("type", "") == "annotation"
            and config.annotation_color_palette_switch
        ):
            annotation_color_palette_list = annotation_color_palette_dict[
                annotation_color_palette
            ]

            # set annotation color
            # get a random color, if the layer is within the number of available color palette colors, grab next color paltte color
            annotation_color = getRandomHexColor()  # set this to random color
            if annotation_layer_count < len(annotation_color_palette_list):
                annotation_color = annotation_color_palette_list[
                    annotation_layer_count % len(annotation_color_palette_list)
                ]
            layer["annotationColor"] = str(annotation_color)
            annotation_layer_count += 1

        # handle mesh layer colors
        if "segmentation" in layer.get("type", "") and config.mesh_color_palette_switch:
            mesh_color_palette_list = mesh_color_palette_dict[mesh_color_palette]
            segments = layer.get("segments", [])
            segmentColors = {}

            # populate segment colors dictionary
            # get a random color, if the layer is within the number of available color palette colors, grab next color paltte color
            mesh_layer_count = 0
            for segment in segments:
                mesh_color = getRandomHexColor()
                if mesh_layer_count < len(mesh_color_palette_list):
                    mesh_color = mesh_color_palette_list[
                        mesh_layer_count % len(mesh_color_palette_list)
                    ]
                segmentColors[segment] = mesh_color
                mesh_layer_count += 1

            # add segment colors dictionary to layer state
            layer["segmentColors"] = segmentColors

    return json.dumps(cdict)


def construct_synapse_state(root_ids: List, flags: dict = None):
    """Construct state for the synapse viewer.

    Args:
        root_ids (list): segment root id
        flags (dict): query parameters
            - pre_synapses
            - post_synapses
            - cleft_layer
            - timestamp

    Returns:
        string: json-formatted state
        dict: synapse stats
    """
    cave_client = CAVEclient(
        "minnie65_phase3_v1", auth_token=os.environ["CAVECLIENT_TOKEN"]
    )
    int_root_ids = [int(x) for x in root_ids]

    # Error checking
    if flags["pre_synapses"] != "True" and flags["post_synapses"] != "True":
        raise Exception(
            "You must pick at least one of the following: Pre-Synapses, Post Synapses"
        )

    # Pre-synapses
    if flags["pre_synapses"] == "True":
        if flags["timestamp"] != "None":
            try:
                pre_synapses = cave_client.materialize.query_table(
                    settings.SYNAPSE_TABLE,
                    filter_in_dict={"pre_pt_root_id": int_root_ids},
                    select_columns=[
                        "ctr_pt_position",
                        "pre_pt_root_id",
                        "post_pt_root_id",
                    ],
                    timestamp=datetime.strptime(flags["timestamp"], "%Y-%m-%d"),
                )
            except Exception as index:
                raise Exception(f"Root ID {index} not found for this timestamp")
        else:
            pre_synapses = cave_client.materialize.query_table(
                settings.SYNAPSE_TABLE,
                filter_in_dict={"pre_pt_root_id": int_root_ids},
                select_columns=["ctr_pt_position", "pre_pt_root_id", "post_pt_root_id"],
            )
        pre_synapses["ctr_pt_position"] = pre_synapses["ctr_pt_position"].apply(
            lambda x: x.tolist()
        )
        pre_synapses["pre_pt_root_id"] = pre_synapses["pre_pt_root_id"].astype(str)
        pre_synapses["post_pt_root_id"] = pre_synapses["post_pt_root_id"].astype(str)

        if len(pre_synapses["ctr_pt_position"]) == 0:
            raise Exception("No pre-synapses found for root ids.")
        position = np.random.choice(pre_synapses["ctr_pt_position"].to_numpy())

    # Post-synapses
    if flags["post_synapses"] == "True":
        if flags["timestamp"] != "None":
            try:
                post_synapses = cave_client.materialize.query_table(
                    settings.SYNAPSE_TABLE,
                    filter_in_dict={"post_pt_root_id": int_root_ids},
                    select_columns=[
                        "ctr_pt_position",
                        "post_pt_root_id",
                        "pre_pt_root_id",
                    ],
                    timestamp=datetime.strptime(flags["timestamp"], "%Y-%m-%d"),
                )
            except Exception as index:
                raise Exception(f"Root ID {index} not found for this timestamp")
        else:
            post_synapses = cave_client.materialize.query_table(
                settings.SYNAPSE_TABLE,
                filter_in_dict={"post_pt_root_id": int_root_ids},
                select_columns=["ctr_pt_position", "post_pt_root_id", "pre_pt_root_id"],
            )
        post_synapses["ctr_pt_position"] = post_synapses["ctr_pt_position"].apply(
            lambda x: x.tolist()
        )
        post_synapses["post_pt_root_id"] = post_synapses["post_pt_root_id"].astype(str)
        post_synapses["pre_pt_root_id"] = post_synapses["pre_pt_root_id"].astype(str)

        if len(post_synapses["ctr_pt_position"]) == 0:
            raise Exception("No post-synapses found for root ids.")
        position = np.random.choice(post_synapses["ctr_pt_position"].to_numpy())

    data_list = [None]
    base_state = create_base_state(root_ids, position)

    # Random color generation
    r = lambda: random.randint(0, 255)
    states = [base_state]
    for root_id in root_ids:
        if flags["pre_synapses"] == "True":
            pre_points = pre_synapses[pre_synapses["pre_pt_root_id"] == root_id][
                "ctr_pt_position"
            ].to_numpy()
            data_list.append(generate_point_df(pre_points))
            states.append(
                create_point_state(
                    name=f"pre_synapses_{root_id}",
                    color="#{:02x}{:02x}{:02x}".format(r(), r(), r()),
                )
            )
        if flags["post_synapses"] == "True":
            post_points = post_synapses[post_synapses["post_pt_root_id"] == root_id][
                "ctr_pt_position"
            ].to_numpy()
            data_list.append(generate_point_df(post_points))
            states.append(
                create_point_state(
                    name=f"post_synapses_{root_id}",
                    color="#{:02x}{:02x}{:02x}".format(r(), r(), r()),
                )
            )

    chained_state = ChainedStateBuilder(states)

    state_dict = chained_state.render_state(return_as="dict", data_list=data_list)
    state_dict["layout"] = "3d"
    state_dict["selectedLayer"] = {"layer": "seg", "visible": True}
    state_dict["jsonStateServer"] = settings.JSON_STATE_SERVER

    # Metrics for each root_id
    synapse_stats = {}

    if flags["pre_synapses"] == flags["post_synapses"] == "True":
        for root_id in root_ids:
            # Pre-Synaptic Metrics
            pre_synapses_slice = pre_synapses[pre_synapses["pre_pt_root_id"] == root_id]
            num_pre_synapses = len(pre_synapses_slice)
            num_pre_targets = len(np.unique(pre_synapses_slice["post_pt_root_id"]))
            pre_synapses_to_targets = round(
                num_pre_synapses / num_pre_targets, ndigits=3
            )

            # Post-Synaptic Metrics
            post_synapses_slice = post_synapses[
                post_synapses["post_pt_root_id"] == root_id
            ]
            num_post_synapses = len(post_synapses_slice)
            num_post_targets = len(np.unique(post_synapses["pre_pt_root_id"]))
            post_synapses_to_targets = round(
                num_post_synapses / num_post_targets, ndigits=3
            )

            # Output to dict
            synapse_stats[root_id] = {
                "pre_synapses": True,
                "num_pre_synapses": num_pre_synapses,
                "num_pre_targets": num_pre_targets,
                "pre_synapses_to_targets": pre_synapses_to_targets,
                "post_synapses": True,
                "num_post_synapses": num_post_synapses,
                "num_post_targets": num_post_targets,
                "post_synapses_to_targets": post_synapses_to_targets,
            }
    # Only Pre-Synaptic Metrics
    elif flags["pre_synapses"] == "True":
        for root_id in root_ids:
            pre_synapses_slice = pre_synapses[pre_synapses["pre_pt_root_id"] == root_id]
            num_pre_synapses = len(pre_synapses_slice)
            num_pre_targets = len(np.unique(pre_synapses_slice["post_pt_root_id"]))
            pre_synapses_to_targets = round(
                num_pre_synapses / num_pre_targets, ndigits=3
            )

            # Output to dict
            synapse_stats[root_id] = {
                "pre_synapses": True,
                "num_pre_synapses": num_pre_synapses,
                "num_pre_targets": num_pre_targets,
                "pre_synapses_to_targets": pre_synapses_to_targets,
            }
    # Only Post-Synaptic Metrics
    else:
        for root_id in root_ids:
            post_synapses_slice = post_synapses[
                post_synapses["post_pt_root_id"] == root_id
            ]
            num_post_synapses = len(post_synapses_slice)
            num_post_targets = len(np.unique(post_synapses["pre_pt_root_id"]))
            post_synapses_to_targets = round(
                num_post_synapses / num_post_targets, ndigits=3
            )

            # Output to dict
            synapse_stats[root_id] = {
                "post_synapses": True,
                "num_post_synapses": num_post_synapses,
                "num_post_targets": num_post_targets,
                "post_synapses_to_targets": post_synapses_to_targets,
            }
    # Append clefts layers to state
    if flags["cleft_layer"] == "True":
        state_dict["layers"].append(
            {
                "type": "segmentation",
                "source": "precomputed://s3://bossdb-open-data/iarpa_microns/minnie/minnie65/clefts-sharded",
                "tab": "source",
                "name": "clefts-sharded",
                "visible": False,
            }
        )
    return json.dumps(state_dict, default=lambda x: [str(y) for y in x]), synapse_stats


def construct_nuclei_state(given_ids: List):
    """Construct state for the synapse viewer.

    Args:
        given_ids (list): nuclei and/or pt_root_ids

    Returns:
        string: json-formatted state
        dict: synapse stats
    """
    given_ids = [int(x) for x in given_ids]
    cave_client = CAVEclient(
        "minnie65_phase3_v1", auth_token=os.environ["CAVECLIENT_TOKEN"]
    )

    soma_df = get_df_from_static(cave_client, settings.NEURON_TABLE)
    soma_df = soma_df[
        (soma_df.id.isin(given_ids)) | (soma_df.pt_root_id.isin(given_ids))
    ]

    # identify inputs that were not found in the table and format to display to user
    ids_not_found = list(set(given_ids) - set().union(soma_df.id, soma_df.pt_root_id))
    formatted_not_found_ids = (
        ", ".join([str(id) for id in ids_not_found]) if len(ids_not_found) else ""
    )

    root_ids = soma_df["pt_root_id"].values
    nuclei_points = np.array(soma_df["pt_position"].values)
    position = (
        nuclei_points[0] if len(nuclei_points) else []
    )  # check what happens when bad values are returned -- add an error case

    if not len(root_ids):
        raise Exception("ID is outdated or does not exist.")

    data_list = [None]
    base_state = create_base_state(root_ids, position)

    # Random color generation
    r = lambda: random.randint(0, 255)
    states = [base_state]

    def generate_cell_type_table(soma_df):
        """Generates Cell type table
        returns filtered list of valid ids (i.e. listed in NUCLEUS_NEURON_SVM table) and their cell types if available, else NaN
        """

        def get_cell_type(nuclei_id, cell_class_df):
            filtered_row = cell_class_df[cell_class_df.id == nuclei_id]
            cell_type = filtered_row.cell_type.values[0] if len(filtered_row) else "NaN"
            return cell_type

        cell_class_info_df = get_df_from_static(cave_client, settings.CELL_CLASS_TABLE)
        cell_class_info_df = cell_class_info_df[
            cell_class_info_df.id.isin(soma_df.id.values)
        ]

        updated_soma_df = pd.merge(soma_df, cell_class_info_df, on="id", how="outer")
        updated_soma_df.cell_type_y = updated_soma_df.cell_type_y.fillna("unknown")

        type_table = "<thead><tr><th>Nuclei ID</th><th>Seg ID</th><th>Type</th></tr></thead><tbody>"
        for nucleus_id, seg_id in zip(
            updated_soma_df.id.values, updated_soma_df.pt_root_id_x.values
        ):
            cell_type = get_cell_type(nucleus_id, cell_class_info_df)
            type_table += (
                "<tr><td>"
                + str(nucleus_id)
                + "</td><td>"
                + str(seg_id)
                + "</td><td>"
                + cell_type
                + "</td><tr>"
            )
        type_table += "</tbody>"

        return type_table, updated_soma_df

    cell_type_table, soma_df = generate_cell_type_table(soma_df)

    for cell_type, type_df in soma_df.groupby("cell_type_y"):
        data_list.append(generate_point_df(np.array(type_df["pt_position_x"].values)))
        states.append(
            create_point_state(
                name=f"{cell_type}_nuclei_points",
                color="#{:02x}{:02x}{:02x}".format(r(), r(), r()),
            )
        )

    chained_state = ChainedStateBuilder(states)

    state_dict = chained_state.render_state(return_as="dict", data_list=data_list)
    state_dict["layout"] = "3d"
    state_dict["selectedLayer"] = {"layer": "seg", "visible": True}
    state_dict["jsonStateServer"] = settings.JSON_STATE_SERVER

    return json.dumps(state_dict), cell_type_table, formatted_not_found_ids


def refresh_ids(ng_state: str, namespace: str):
    namespace = Namespace.objects.get(namespace=namespace)
    if not namespace.refresh_selected_root_ids:
        return ng_state

    if namespace.pcg_source == PcgChoices.PINKY:
        return ng_state
    else:
        cave_client = CAVEclient(
            "minnie65_phase3_v1", auth_token=os.environ["CAVECLIENT_TOKEN"]
        )

    state = json.loads(ng_state)
    for layer in state["layers"]:
        if layer["type"] == "segmentation_with_graph" and len(
            layer.get("segments", [])
        ):
            latest_ids = set()
            for root_id in layer["segments"]:
                try:
                    roots = cave_client.chunkedgraph.get_latest_roots(root_id).tolist()
                    roots = list(map(str, roots))
                    latest_ids.update(roots)
                except Exception as e:
                    logging.error(f"CaveClient Exception: {e}")
                    return ng_state

            layer["segments"] = list(latest_ids)
    return json.dumps(state)
