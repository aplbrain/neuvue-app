from django.conf import settings
import pandas as pd 
import numpy as np 
from typing import List
from nglui.statebuilder import (
    ImageLayerConfig, 
    SegmentationLayerConfig, 
    AnnotationLayerConfig, 
    LineMapper,
    StateBuilder,
    ChainedStateBuilder
    )


def create_base_state(seg_ids, coordinate):
    """Generates a base state containing imagery and segemntation layers. 

    Args:
        seg_ids (list): seg_ids to select in the view
        coordinate (tuple|list): collection of three integer voxel coordinates, XYZ order.

    Returns:
        StateBuilder: Base State
    """
    
    # Create ImageLayerConfig
    img_source = "precomputed://" + settings.IMAGE_SOURCE
    black = settings.CONTRAST.get("black", 0)
    white = settings.CONTRAST.get("white", 1)
    img_layer = ImageLayerConfig(
        name='em',
        source=img_source, 
        contrast_controls=True, 
        black=black, 
        white=white
        )
    
    # Create SegmentationLayerConfig
    seg_source = "graphene://" + settings.PROD_PCG_SOURCE
    seg_layer = SegmentationLayerConfig(
        name='seg', 
        source=seg_source, 
        fixed_ids=seg_ids)
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
    point_column_a = []
    point_column_b = []

    for i in range(points.shape[0] - 1):
        point_column_a.append(points[i])
        point_column_b.append(points[i+1])

    point_column_a = np.concatenate(point_column_a).tolist()
    point_column_b = np.concatenate(point_column_b).tolist()
    return pd.DataFrame(
        {
            "point_column_a": point_column_a,
            "point_column_b": point_column_b,
            "group": np.ones(len(point_column_a)),
        }
    )

def create_path_state():
    """Create the annotation state for paths.

    Returns:
        StateBuilder: Annotation State
    """
    anno = AnnotationLayerConfig("selected_paths",
        mapping_rules=LineMapper("point_column_a", "point_column_b", group_column="group"),
    )
    return StateBuilder(layers=[anno], resolution=settings.VOXEL_RESOLUTION)

def construct_proofreading_url(seg_ids, coordinate, points):
    path_df = generate_path_df(points)
    base_state = create_base_state(seg_ids, coordinate)
    path_state = create_path_state()
    pf_state = ChainedStateBuilder([base_state, path_state])

    return pf_state.render_state(
        [None, path_df], return_as='url', url_prefix=settings.NG_CLIENT
    )