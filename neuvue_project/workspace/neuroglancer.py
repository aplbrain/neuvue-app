from django.conf import settings
import pandas as pd 
import numpy as np 
from typing import List
import json
import requests
import os 

from nglui.statebuilder import (
    ImageLayerConfig, 
    SegmentationLayerConfig, 
    AnnotationLayerConfig, 
    LineMapper,
    PointMapper,
    StateBuilder,
    ChainedStateBuilder
    )

from .models import Namespace, NeuroglancerLinkType

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_base_state(seg_ids, coordinate, namespace):
    """Generates a base state containing imagery and segemntation layers. 

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


def create_point_state(use_description=False):
    """Create the annotation state for points.
    Dontt tuse linemapper, just creates a neuroglancer link that is just Points
    nglui statebuilder
    Returns:
        StateBuilder: Annotation State
    """
    if use_description:
        anno = AnnotationLayerConfig("annotations",
            mapping_rules=PointMapper(
                "point_column_a", 
                group_column="group", 
                description_column="description",
                set_position=False),
        )
    else:
        anno = AnnotationLayerConfig("annotations",
            mapping_rules=PointMapper("point_column_a", group_column="group", set_position=False),
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

def get_from_state_server(url: str): 
    """Gets JSON state string from state server

    Args:
        url (str): json state server link
    Returns:
        (str): JSON String 
    """
    resp = requests.get(url)
    # Make sure its a json string
    if 'json' in resp.headers.get('content-type'):
        return resp.text
    else:
        return "{}"


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
        'Authorization': os.environ['CaveclientToken']
    }

    # Post! 
    resp = requests.post(settings.JSON_STATE_SERVER, data=json.dumps(state), headers=headers)

    # Response will contain the URL for the state you just posted
    return resp.text

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
    