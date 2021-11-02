from django.conf import settings
import pandas as pd 
import numpy as np 
from typing import List
from nglui.statebuilder import (
    ImageLayerConfig, 
    SegmentationLayerConfig, 
    AnnotationLayerConfig, 
    LineMapper,
    PointMapper,
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
    img_source = "precomputed://" + settings.IMG_SOURCE
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

def create_path_state():
    """Create the annotation state for paths.

    Returns:
        StateBuilder: Annotation State
    """
    anno = AnnotationLayerConfig("selected_paths",
        mapping_rules=LineMapper("point_column_a", "point_column_b", group_column="group"),
    )
    return StateBuilder(layers=[anno], resolution=settings.VOXEL_RESOLUTION)

def create_point_state():
    """Create the annotation state for points.
    Dontt tuse linemapper, just creates a neuroglancer link that is just Points
    nglui statebuilder
    Returns:
        StateBuilder: Annotation State
    """
    anno = AnnotationLayerConfig("selected_paths",
        mapping_rules=PointMapper("point_column_a", group_column="group"),
    )
    # If statement that checks using a new arg, namespace, and checks string to see what task type it is
    # splitt uses creatte_pattth_statte
    # all currently use create base state
    # new one, tracing, uses base staet, and new layer with annotation points


    return StateBuilder(layers=[anno], resolution=settings.VOXEL_RESOLUTION)

def construct_proofreading_url(seg_ids, coordinate, namespace="split", points=np.NaN):
    base_state = create_base_state(seg_ids, coordinate)
    if points.any():
        path_df = generate_path_df(points)
        if namespace == "split":
            state = create_path_state()
        elif namespace == "trace":
            state = create_point_state()
        else:
            raise ValueError("")
        pf_state = ChainedStateBuilder([base_state, state])
    else:
        return base_state.render_state(return_as='url', url_prefix=settings.NG_CLIENT)

    return pf_state.render_state(
        [None, path_df], return_as='url', url_prefix=settings.NG_CLIENT
    )