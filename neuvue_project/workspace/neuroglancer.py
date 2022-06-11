from django.conf import settings
from django.apps import apps
import pandas as pd 
import numpy as np 
from caveclient import CAVEclient
from typing import List
from datetime import datetime
import json
import requests
import os 
import backoff
import random


from nglui.statebuilder import (
    ImageLayerConfig, 
    SegmentationLayerConfig, 
    AnnotationLayerConfig, 
    LineMapper,
    PointMapper,
    StateBuilder,
    ChainedStateBuilder
    )

from .models import Namespace, NeuroglancerLinkType, PcgChoices

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Config = apps.get_model('preferences', 'Config')

def create_base_state(seg_ids, coordinate, namespace):
    """Generates a base state containing imagery and segmentation layers. 

    Args:
        seg_ids (list): seg_ids to select in the view
        coordinate (tuple|list): collection of three integer voxel coordinates, XYZ order.
        namespace (str): task namespace
    Returns:
        StateBuilder: Base State
    """
    
    # Create ImageLayerConfig
    img_source = "precomputed://" + Namespace.objects.get(namespace = namespace).img_source
    try: 
        black = settings.DATASET_VIEWER_OPTIONS[img_source]['contrast']["black"]
        white = settings.DATASET_VIEWER_OPTIONS[img_source]['contrast']["white"]
    except KeyError:
        black = 0
        white = 1
    
    img_layer = ImageLayerConfig(
        name='em',
        source=img_source, 
        contrast_controls=True, 
        black=black, 
        white=white
        )
    
    # Create SegmentationLayerConfig
    seg_source = "graphene://" + Namespace.objects.get(namespace = namespace).pcg_source
    segmentation_view_options = {
        'alpha_selected': 0.6,
        'alpha_3d': 0.3
        }
    seg_layer = SegmentationLayerConfig(
        name='seg', 
        source=seg_source, 
        fixed_ids=seg_ids,
        view_kws=segmentation_view_options
        )
    view_options = {'position': coordinate, 'zoom_image': 20}

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
                "description": description
            }
        )
    else:
        return pd.DataFrame({"point_column_a": point_column_a, "group": group})


def create_path_state():
    """Create the annotation state for paths.

    Returns:
        StateBuilder: Annotation State
    """
    path = AnnotationLayerConfig("selected_paths", active=False,
        mapping_rules=LineMapper("point_column_a", "point_column_b", group_column="group"),
    )
    anno = AnnotationLayerConfig("merge_point")
    return StateBuilder(layers=[path, anno], resolution=settings.VOXEL_RESOLUTION)


def create_point_state(name='annotations', group=None, description=None, color=None):
    """Create the annotation state for points.
    Dontt tuse linemapper, just creates a neuroglancer link that is just Points
    nglui statebuilder
    Returns:
        StateBuilder: Annotation State
    """
    anno = AnnotationLayerConfig(name,
        mapping_rules=PointMapper(
            "point_column_a", 
            group_column=group, 
            description_column=description,
            set_position=False),
        color=color
    )

    return StateBuilder(layers=[anno], resolution=settings.VOXEL_RESOLUTION)


def construct_proofreading_state(task_df, points, return_as='json'):
    """Generates a Neuroglancer URL with the path/annotation information preloaded.

    Args:
        task_df (pandas.DataFrame): Task Dataframe from Neuvue-Client
        points (List): List of coordinates of the initial set of Point Objects

    Returns:
        string: Neuroglancer URL
    """
    # TODO: Automatically iterate through Namespaces and map them to the 
    # appropriate Neuroglancer functions. 
    seg_ids = [task_df['seg_id']]
    base_state = create_base_state(seg_ids, points[0], task_df['namespace'])

    # Get any annotation coordinates. Append original points.
    coordinates = task_df['metadata'].get('coordinates', [])

    # Create a list of dataframes used for state creation. Since first state is 
    # the base layer, the first element is None. 
    data_list = [None]
    ng_type = Namespace.objects.get(namespace = task_df['namespace']).ng_link_type
    if ng_type == NeuroglancerLinkType.PATH:

        if points:
            # Append start and end soma coordinates
            coordinates.insert(0 ,points[0])
            coordinates.append(points[-1])
            coordinates = np.array(coordinates)
        
        data_list.append( generate_path_df(coordinates))
        path_state = create_path_state()
        chained_state = ChainedStateBuilder([base_state, path_state])
    
    elif ng_type == NeuroglancerLinkType.POINT: 
        # Get grouping and annotation descriptions, if they exist
        coordinates = np.array(coordinates)
        group = task_df['metadata'].get('group')
        description = task_df['metadata'].get('description')
        data_list.append( generate_point_df(coordinates, description=description, group=group))
        point_state = create_point_state(bool(description))
        chained_state = ChainedStateBuilder([base_state, point_state])

    elif ng_type == NeuroglancerLinkType.PREGENERATED and task_df.get('ng_state'):
        if return_as == 'json':
            return task_df['ng_state']
        elif return_as == 'url':
            return construct_url_from_existing(json.dumps(task_df['ng_state']))
    
    return chained_state.render_state(
            data_list, return_as=return_as, url_prefix=settings.NG_CLIENT
        )
    
def construct_url_from_existing(state: str):
    return settings.NG_CLIENT + '/#!' + state

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def get_from_state_server(url: str): 
    """Gets JSON state string from state server

    Args:
        url (str): json state server link
    Returns:
        (str): JSON String 
    """
    headers = {
        'content-type': 'application/json',
        'Authorization': f"Bearer {os.environ['CAVECLIENT_TOKEN']}"
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
        'content-type': 'application/json',
        'Authorization': f"Bearer {os.environ['CAVECLIENT_TOKEN']}"
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
    if state_obj.get('value'):
        return json.dumps(state_obj['value'])
    else:
        return raw_state

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def _get_lineage_graph(root_id:str, cave_client):
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
        return cave_client.chunkedgraph.get_lineage_graph([root_id], timestamp_past=datetime(year=2021, month=11, day=1), as_nx_graph=True)
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
        soma_df = cave_client.materialize.query_table('nucleus_neuron_svm', filter_in_dict={
            'pt_root_id': root_ids[:3]
        })
        if not len(soma_df):
            soma_df = cave_client.materialize.query_table('nucleus_neuron_svm', filter_in_dict={
            'pt_root_id': root_ids
            })
        if len(soma_df) > 3:
            soma_df = soma_df.head(3)
        pt_position = soma_df.iloc[0]['pt_position']
        present_root_ids = list(soma_df['pt_root_id'])
    except IndexError as e:
        logging.error(e)
        raise Exception('Unable to find Soma Center')
    except Exception as e:
        logging.error(e)
        raise Exception(e)
    return pt_position, present_root_ids

def _get_nx_graph_image(nx_graph):
    def networkx_to_graphViz(nx_graph):
        import graphviz
        import networkx as nx
        gv_graph = graphviz.Digraph('lineage',format = 'svg',graph_attr={'size':'6,{}','ratio':"compress",'ranksep':'0.5'},node_attr={'fontsize':'18','fontname':"Arial"}) # 'size':'6,3',
        timestamps = nx.get_node_attributes(nx_graph, "timestamp") # dictionary of all timestamps in the graph, key: node
        operation_ids = nx.get_node_attributes(nx_graph, "operation_id") # dictionary of all operation ids in the graph, key: node
        for node in nx_graph.nodes():
            label_str = str(node)
            label_str += '\n' + datetime.fromtimestamp(timestamps.get(node)).strftime('%Y-%m-%d') if timestamps.get(node) else '' # add timestamp if it exists
            label_str +=  '\n id: ' + str(operation_ids.get(node)) if operation_ids.get(node) else '' # add operation id if it exists
            gv_graph.node(str(node),label=label_str)
        for edge0, edge1 in nx_graph.edges():
            gv_graph.edge(str(edge0), str(edge1))
        gv_graph = gv_graph.unflatten(stagger=10) 
        return gv_graph.pipe(encoding='utf-8')
    return networkx_to_graphViz(nx_graph)

def construct_lineage_state_and_graph(root_id:str):
    """Construct state for the lineage viewer.

    Args:
        root_id (str): segment root id

    Returns:
        string: json-formatted state
    """
    root_id = root_id.strip()
    cave_client = CAVEclient('minnie65_phase3_v1',  auth_token=os.environ['CAVECLIENT_TOKEN'])

    # Lineage graph gives you the nodes and edges of a root IDs history
    lineage_graph = _get_lineage_graph(root_id, cave_client)
    graph_image = _get_nx_graph_image(lineage_graph)
    # We need the root ids and a position to create a base state.
    # Since this is not part of any particular namespace, I chose automatedSplit 
    # to ensure the neuroglancer state uses Minnie data. 
    root_ids = {str(x) for x in lineage_graph}

    # Ensure original root ID is in list of shown IDs
    root_ids.add(root_id)
    root_ids = list(root_ids)
    position, root_ids_with_center = _get_soma_center(root_ids, cave_client)
    base_state = create_base_state(root_ids_with_center, position, 'automatedSplit')

    # For the rest of the IDs, we can add them to the seg layer as unselected.
    base_state_dict = base_state.render_state(return_as='dict')
    base_state_dict['layout'] = '3d'
    base_state_dict["selectedLayer"] = {"layer": "seg", "visible": True}
    for layer in base_state_dict['layers']:
        if layer['name'] == 'seg':
            layer['hiddenSegments'] = root_ids[3:]

    return json.dumps(base_state_dict), graph_image

def apply_state_config(state:str, username:str):
    cdict = json.loads(state)
    cdict['jsonStateServer'] = settings.JSON_STATE_SERVER
    #make ng state preferences changes, json string to dict
    try:
        config = Config.objects.filter(user=username).order_by('-id')[0]
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

    cdict = json.loads(state)

    if config.layout_switch:
        cdict["layout"] = str(layout)
    if config.gpu_limit_switch:
        cdict["gpuMemoryLimit"] = int(float(gpu_limit) * 1E9)
    if config.sys_limit_switch:
        cdict["systemMemoryLimit"] = int(float(sys_limit) * 1E9)
    if config.chunk_requests_switch:
        cdict["concurrentDownloads"] = int(chunk_requests)

    if config.zoom_level_switch:
        cdict["navigation"]["zoomFactor"] = int(zoom_level)
    
    # create color palette dictionary
    annotation_color_palette_dict = {'palette1' : ['#F9C80E', '#F86624', '#EA3546', '#662E9B', '#43BCCD'],
                            'palette2' : ['#006D77', '#83C5BE', '#EFG6F9', '#FFDDD2', '#E29578'], 
                            'palette3' : ['#22577A', '#38A3A5', '#57CC99', '#80ED99', '#C7F9CC'], 
                            'palette4' : ['#25CED1', '#FFFFFF', '#FCEADE', '#FF8A5B', '#EA526F'], 
                            'palette5' : ['#335C67', '#FFF3B0', '#E09F3E', '#9E2A2B', '#540B0E'], 
                            'palette6' : ['#FF99C8', '#FCF6BD', '#D0F4DE', '#A9DEF9', '#E4C1F9']}

    # create mesh color palette dictionary
    mesh_color_palette_dict = {'palette1' : ['#F9C80E', '#F86624', '#EA3546', '#662E9B', '#43BCCD'],
                        'palette2' : ['#006D77', '#83C5BE', '#EFG6F9', '#FFDDD2', '#E29578'], 
                        'palette3' : ['#22577A', '#38A3A5', '#57CC99', '#80ED99', '#C7F9CC'], 
                        'palette4' : ['#25CED1', '#FFFFFF', '#FCEADE', '#FF8A5B', '#EA526F'], 
                        'palette5' : ['#335C67', '#FFF3B0', '#E09F3E', '#9E2A2B', '#540B0E'], 
                        'palette6' : ['#FF99C8', '#FCF6BD', '#D0F4DE', '#A9DEF9', '#E4C1F9']}


    
    annotation_layer_count = 0
    for layer in cdict['layers']:
        # handle alpha
        if 'segmentation' in layer.get('type', '') and config.alpha_selected_switch:
            layer['selectedAlpha'] = float(alpha_selected)
        
        if 'segmentation' in layer.get('type', '') and config.alpha_3d_switch:
            layer['objectAlpha'] = float(alpha_3d)
        
        # handle annotation layer colors
        if layer.get('type', '') == 'annotation' and config.annotation_color_palette_switch:
            annotation_color_palette_list = annotation_color_palette_dict[annotation_color_palette]
            annotation_color = annotation_color_palette_list[annotation_layer_count%len(annotation_color_palette_list)]
            layer['annotationColor'] = str(annotation_color)
            annotation_layer_count += 1
    
        # handle mesh layer colors
        if 'segmentation' in layer.get('type', '') and config.mesh_color_palette_switch:
            mesh_color_palette_list = mesh_color_palette_dict[mesh_color_palette]
            segments = layer['segments']
            segmentColors = {}

            # populate segment colors dictionary
            mesh_layer_count = 0
            for segment in segments:
                mesh_color = mesh_color_palette_list[mesh_layer_count%len(mesh_color_palette_list)]
                segmentColors[segment] = mesh_color
                mesh_layer_count += 1
            
            # add segment colors dictionary to layer state
            layer['segmentColors'] = segmentColors



    return json.dumps(cdict)

def construct_synapse_state(root_ids:List):
    """Construct state for the synapse viewer.

    Args:
        root_id (str): segment root id

    Returns:
        string: json-formatted state
        dict: synapse stats
    """
    cave_client = CAVEclient('minnie65_phase3_v1',  auth_token=os.environ['CAVECLIENT_TOKEN'])
    
    pre_synapses = cave_client.materialize.query_table(
    "synapses_pni_2", 
    filter_in_dict={"pre_pt_root_id": root_ids},
     select_columns=['ctr_pt_position', 'pre_pt_root_id']
    )

    post_synapses = cave_client.materialize.query_table(
        "synapses_pni_2", 
        filter_in_dict={"post_pt_root_id": root_ids},
        select_columns=['ctr_pt_position', 'post_pt_root_id']
    )
    pre_synapses['ctr_pt_position'] = pre_synapses['ctr_pt_position'].apply(lambda x: x.tolist())
    pre_synapses['pre_pt_root_id'] = pre_synapses['pre_pt_root_id'].astype(str)
    post_synapses['post_pt_root_id']= post_synapses['post_pt_root_id'].astype(str)
    post_synapses['ctr_pt_position'] = post_synapses['ctr_pt_position'].apply(lambda x: x.tolist())
    
    if len(pre_synapses['ctr_pt_position']) == 0 and len(post_synapses['ctr_pt_position']) == 0:
        raise Exception('No pre or post synapses found for root ids.')
    
    position = np.random.choice(pre_synapses['ctr_pt_position'].to_numpy())
    

    data_list = [None]
    base_state = create_base_state(root_ids, position, 'automatedSplit')
    # Random color generation
    r = lambda: random.randint(0,255)
    states = [base_state]
    for root_id in root_ids:
        pre_points = pre_synapses[pre_synapses["pre_pt_root_id"]==root_id]['ctr_pt_position'].to_numpy()
        post_points = post_synapses[post_synapses["post_pt_root_id"]==root_id]['ctr_pt_position'].to_numpy()

        data_list.append( generate_point_df( pre_points))
        data_list.append( generate_point_df( post_points))
    
        states.append( create_point_state(name=f'pre_synapses_{root_id}', color='#{:02x}{:02x}{:02x}'.format(r(), r(), r())))
        states.append( create_point_state(name=f'post_synapses_{root_id}', color='#{:02x}{:02x}{:02x}'.format(r(), r(), r())))
    
    chained_state = ChainedStateBuilder(states)
    
    state_dict = chained_state.render_state(return_as='dict', data_list=data_list)
    state_dict['layout'] = '3d'
    state_dict["selectedLayer"] = {"layer": "seg", "visible": True}
    state_dict['jsonStateServer'] = settings.JSON_STATE_SERVER
    
    synapse_stats = {}
    
    for root_id in root_ids:
        synapse_stats[root_id] = {
            "num_pre": len(pre_synapses[pre_synapses['pre_pt_root_id']==root_id]),
            "num_post": len(post_synapses[post_synapses['post_pt_root_id']==root_id])
        }

    # Append clefts layers to state 
    state_dict['layers'].append({
        "type": "segmentation",
        "source": "precomputed://s3://bossdb-open-data/iarpa_microns/minnie/minnie65/clefts-sharded",
        "tab": "source",
        "name": "clefts-sharded",
        "visible": False
    })
    return json.dumps(state_dict), synapse_stats

def refresh_ids(ng_state:str, namespace:str): 
    namespace = Namespace.objects.get(namespace=namespace)
    if not namespace.refresh_selected_root_ids:
        return ng_state
    
    if namespace.pcg_source == PcgChoices.PINKY:
        return ng_state
    else:
        cave_client = CAVEclient('minnie65_phase3_v1',  auth_token=os.environ['CAVECLIENT_TOKEN'])
    
    state = json.loads(ng_state)
    for layer in state['layers']:
        if layer['type'] == "segmentation_with_graph" and len(layer.get("segments", [])):
            latest_ids = set()
            for root_id in layer['segments']:
                try:
                    roots = cave_client.chunkedgraph.get_latest_roots(root_id).tolist()
                    roots = list(map(str, roots))
                    latest_ids.update(roots)
                except Exception as e:
                    logging.error(f"CaveClient Exception: {e}")
                    return ng_state

            layer['segments'] = list(latest_ids)
    return json.dumps(state)