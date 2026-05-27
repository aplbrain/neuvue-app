from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import requests
import math
from django.conf import settings
from nglui.statebuilder import (
    StateBuilder,
    AnnotationLayerConfig,
    LineMapper,
    site_utils,
)
import json
import pandas as pd
import numpy as np
import base64


DEFAULT_COMPARTMENT_COLORS = {
    "axon": "#ff4d4d",
    "dendrite": "#4d9dff",
    "basal": "#45c46f",
    "apical": "#d977ff",
    "apical_tuft": "#ffd24d",
    "apical_shaft": "#ff944d",
    "oblique": "#00c2a8",
}

@dataclass
class PluginOutput:
    """
    Data class to encapsulate the results of modifying a Neuroglancer state.
    
    Attributes:
        modified_state (Dict[str, Any]): The updated Neuroglancer state.
        status_code (int): Status code indicating success or specific error conditions.
        message (str): Message intended for user notifications (e.g., via a toast pop-up).
        additional_info (Dict[str, Any]): Extra details from the plugin, such as logs or stderr output.
    """
    modified_state: Dict[str, Any]
    status_code: int
    message: str
    additional_info: Dict[str, Any]


class NeuroglancerPlugin(ABC):
    """
    Abstract base class for Neuroglancer state modification plugins within the NeuVue proofreading framework.
    
    Subclasses must implement the modify_state method to take a Neuroglancer state,
    perform plugin-specific modifications (e.g. adding an annotation layer with soma locations),
    and return both the new state and a payload with status and ancillary information.
    """
    
    def __init__(self, **params):
        """
        Initialize the plugin with optional configuration parameters.
        
        Args:
            **params: Arbitrary keyword arguments that serve as default configuration for the plugin.
        """
        self.params = params

    @abstractmethod
    def modify_state(self, state: Dict[str, Any], **kwargs) -> PluginOutput:
        """
        Modify the given Neuroglancer state and return the modified state along with a payload.
        
        This method should:
          - Process the input state.
          - Return a new or updated state.
          - Provide a payload containing a status code, a user message, 
            and any additional information such as logs or stderr output.
        
        Args:
            state (Dict[str, Any]): The original Neuroglancer state.
        
        Returns:
            PluginOutput: An instance containing the updated state, status code, message, and additional information.
        """
        pass


class TestNeuroglancerPlugin(NeuroglancerPlugin):
    """
    A test implementation of the NeuroglancerPlugin for demonstration purposes.
    
    This plugin simply returns the original state with a slightly modified position with a success message 
    and a status code of 200.
    """
    
    def __init__(self, **params):
        """
        Initialize the plugin with a default layer name and other optional parameters.
        
        Args:
            layer_name (str): The name for the soma annotation layer.
            **params: Additional configuration parameters.
        """
        super().__init__(**params)

    def modify_state(self, state: Dict[str, Any], **kwargs) -> PluginOutput:
        # For testing, we just return the original state in a slightly modified position
        offset =  self.params.get("offset", 0)
        state['position'] = [state['position'][0]+offset, state['position'][1]+offset, state['position'][2]+offset]
        return PluginOutput(
            modified_state=state,
            status_code=200,
            message="Plugin executed successfully.",
            additional_info={"test": "This is a test plugin."}
        )

class NeurdSkeletonPointsPlugin(NeuroglancerPlugin):
    """
    This plugin queries NEURD for the skeletons of all selected seg IDs and
    adds them to the ng state as a new annotation layer.
    """
    def __init__(self, **params):
        super().__init__(**params)
        self.dataset_schema = params.get("dataset_schema")
        self.resolution = params.get("resolution")
        self.base_url = settings.NEURD_LAMBDA_URL
        self.endpoint = params.get("endpoint", "labeled_skeleton")
        self.request_timeout = params.get("request_timeout", 30)
        self.compartment_colors = {
            **DEFAULT_COMPARTMENT_COLORS,
            **params.get("compartment_colors", {}),
        }

    def modify_state(self, state: Dict[str, Any], **kwargs) -> PluginOutput:
        dataset_schema = self.dataset_schema
        resolution = self._validated_resolution()

        if not dataset_schema:
            return PluginOutput(
                modified_state=state,
                status_code=400,
                message=(
                    "NEURD skeleton plugin is missing required plugin parameter "
                    "`dataset_schema`."
                ),
                additional_info={},
            )

        if resolution is None:
            return PluginOutput(
                modified_state=state,
                status_code=400,
                message=(
                    "NEURD skeleton plugin is missing or has an invalid required "
                    "plugin parameter `resolution`; expected a three-value list "
                    "such as [x, y, z]."
                ),
                additional_info={"dataset_schema": dataset_schema},
            )

        # Get seg ids to query
        seg_ids = self._segment_ids(kwargs.get("plugin_inputs"))
        position = state["position"]

        if not seg_ids:
            return PluginOutput(
                modified_state=state,
                status_code=400,
                message=(
                    "NEURD skeleton plugin requires a segment ID. Paste a segment "
                    "ID into the plugin input and try again."
                ),
                additional_info={
                    "dataset_schema": dataset_schema,
                    "required_input": "segment_id",
                },
            )

        if not settings.NEURD_LAMBDA_URL:
            return PluginOutput(
                modified_state=state,
                status_code=500,
                message="NEURD skeleton plugin is not configured: NEURD_LAMBDA_URL is empty.",
                additional_info={},
            )

        if not settings.NEURD_LAMBDA_SECRET_ARN:
            return PluginOutput(
                modified_state=state,
                status_code=500,
                message=(
                    "NEURD skeleton plugin is not configured: "
                    "NEURD_LAMBDA_SECRET_ARN is empty."
                ),
                additional_info={},
            )

        # Query for skeleton
        skeletons_by_compartment = {}
        for seg_id in seg_ids:
            if '!' not in seg_id:
                request_url = f"{self.base_url}/{self.endpoint}/{seg_id}"
                try:
                    secret = base64.b64encode(settings.NEURD_LAMBDA_SECRET_ARN.encode("utf-8")).decode("utf-8")
                    headers = {'Authorization': f'Bearer {secret}'}
                    params = self._request_params(dataset_schema)
                    response = requests.get(
                        request_url,
                        headers=headers,
                        params=params,
                        timeout=self.request_timeout,
                    )
                    # Raise exception if request is unsuccessful
                    response.raise_for_status()
                    # Process the successful response
                    skeleton_points = json.loads(response.text)["skeleton_points"]
                    if isinstance(skeleton_points, dict):
                        for compartment, skeleton in skeleton_points.items():
                            skeletons_by_compartment.setdefault(compartment, []).extend(
                                skeleton
                            )
                    else:
                        skeletons_by_compartment.setdefault("neurd skeleton", []).extend(
                            skeleton_points
                        )
                except requests.Timeout:
                    return PluginOutput(
                        modified_state=state,
                        status_code=504,
                        message=(
                            f"NEURD skeleton request timed out for segment {seg_id} "
                            f"after {self.request_timeout} seconds."
                        ),
                        additional_info={
                            "dataset_schema": dataset_schema,
                            "request_url": request_url,
                        },
                    )
                except requests.HTTPError as e:
                    return PluginOutput(
                        modified_state=state,
                        status_code=response.status_code,
                        message=(
                            f"NEURD skeleton request failed for segment {seg_id} "
                            f"with status {response.status_code}: "
                            f"{self._response_error_text(response)}"
                        ),
                        additional_info={
                            "dataset_schema": dataset_schema,
                            "request_url": request_url,
                        },
                    )
                except requests.RequestException as e:
                    return PluginOutput(
                        modified_state=state,
                        status_code=502,
                        message=(
                            f"Could not reach the NEURD skeleton service for segment "
                            f"{seg_id}: {e}"
                        ),
                        additional_info={
                            "dataset_schema": dataset_schema,
                            "request_url": request_url,
                        },
                    )
                except (KeyError, json.JSONDecodeError, TypeError) as e:
                    return PluginOutput(
                        modified_state=state,
                        status_code=502,
                        message=(
                            f"NEURD skeleton service returned an unexpected response "
                            f"for segment {seg_id}: {e}"
                        ),
                        additional_info={
                            "dataset_schema": dataset_schema,
                            "request_url": request_url,
                        },
                    )
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    return PluginOutput(
                        modified_state=state,
                        status_code=500,
                        message=(
                            f"Unexpected NEURD skeleton plugin error for segment "
                            f"{seg_id}: {e}"
                        ),
                        additional_info={"dataset_schema": dataset_schema}
                    )

        layer_configs = []
        layer_dfs = []
        for compartment, skeleton in skeletons_by_compartment.items():
            skeleton_df = self._skeleton_segments_df(skeleton, resolution)
            if skeleton_df.empty:
                continue

            layer_name = self._layer_name(compartment)
            layer_configs.append(
                AnnotationLayerConfig(
                    name=layer_name,
                    color=self.compartment_colors.get(compartment, "white"),
                    mapping_rules=LineMapper(
                        "point_column_a",
                        "point_column_b",
                        group_column="group",
                    ),
                )
            )
            layer_dfs.append(skeleton_df)

        if not layer_configs:
            return PluginOutput(
                modified_state=state,
                status_code=404,
                message=(
                    "No NEURD skeleton points were found for the selected segments "
                    f"using dataset_schema={dataset_schema}."
                ),
                additional_info={
                    "dataset_schema": dataset_schema,
                    "selected_segments": seg_ids,
                },
            )
        
        # add to state
        site_utils.set_default_config(target_site='spelunker')
        view_options = {'position': [position[0]*2, position[1]*2, position[2]]}
        try:
            final_state = state
            for layer_config, layer_df in zip(layer_configs, layer_dfs):
                state_builder = StateBuilder(
                    [layer_config],
                    base_state=final_state,
                    view_kws=view_options,
                )
                final_state = state_builder.render_state(layer_df, return_as="dict")
        except Exception as e:
            return PluginOutput(
                modified_state=state,
                status_code=500,
                message=f"NEURD skeleton plugin could not render skeleton layers: {e}",
                additional_info={
                    "dataset_schema": dataset_schema,
                    "selected_segments": seg_ids,
                    "layer_names": [layer_config.name for layer_config in layer_configs],
                },
            )

        # Return modified state
        return PluginOutput(
            modified_state=final_state,
            status_code=200,
            message="Plugin executed successfully.",
            additional_info={"dataset_schema": dataset_schema}
        )

    def _request_params(self, dataset_schema):
        params = {"dataset_schema": dataset_schema}
        for name in ("split_index", "decimation_ratio"):
            if self.params.get(name) is not None:
                params[name] = self.params[name]
        return params

    def _segment_ids(self, plugin_inputs):
        plugin_inputs = plugin_inputs or {}
        raw_segment_ids = (
            plugin_inputs.get("segment_id")
            or plugin_inputs.get("seg_id")
            or plugin_inputs.get("segment_ids")
        )
        if raw_segment_ids in (None, ""):
            return []
        if isinstance(raw_segment_ids, (list, tuple)):
            return [
                str(segment_id).strip()
                for segment_id in raw_segment_ids
                if str(segment_id).strip()
            ]
        return [
            segment_id
            for segment_id in str(raw_segment_ids)
            .replace(",", " ")
            .split()
            if segment_id
        ]

    def _validated_resolution(self):
        if self.resolution in (None, ""):
            return None

        if not isinstance(self.resolution, (list, tuple)) or len(self.resolution) != 3:
            return None

        try:
            return [float(value) for value in self.resolution]
        except (TypeError, ValueError):
            return None

    def _skeleton_segments_df(self, skeleton, resolution):
        point_column_a = []
        point_column_b = []
        for point_a, point_b in self._line_segments(skeleton):
            point_column_a.append(self._to_voxel(point_a, resolution))
            point_column_b.append(self._to_voxel(point_b, resolution))

        return pd.DataFrame(
            {
                "point_column_a": point_column_a,
                "point_column_b": point_column_b,
                "group": [1] * len(point_column_a),
            }
        )

    def _line_segments(self, skeleton):
        if skeleton is None or (isinstance(skeleton, str) and skeleton == ""):
            return []

        try:
            skeleton_array = np.asarray(skeleton, dtype=float)
        except (TypeError, ValueError):
            skeleton_array = None

        if skeleton_array is not None:
            if skeleton_array.size == 0:
                return []
            if skeleton_array.ndim == 3 and skeleton_array.shape[1:] == (2, 3):
                return self._valid_segments(
                    (
                        self._point_tuple(segment[0]),
                        self._point_tuple(segment[1]),
                    )
                    for segment in skeleton_array
                )
            if skeleton_array.ndim == 2 and skeleton_array.shape[1] == 3:
                return self._valid_segments(
                    (
                        self._point_tuple(skeleton_array[index]),
                        self._point_tuple(skeleton_array[index + 1]),
                    )
                    for index in range(len(skeleton_array) - 1)
                )

        return self._line_segments_from_nested_data(skeleton)

    def _line_segments_from_nested_data(self, skeleton):
        segment = self._segment_tuple(skeleton)
        if segment is not None:
            return [segment]

        try:
            items = list(skeleton)
        except TypeError:
            return []

        points = []
        segments = []
        for item in items:
            segment = self._segment_tuple(item)
            if segment is not None:
                segments.append(segment)
                continue

            point = self._point_tuple(item)
            if point is not None:
                points.append(point)
                continue

            segments.extend(self._line_segments_from_nested_data(item))

        if segments:
            return segments

        return [
            (points[index], points[index + 1])
            for index in range(len(points) - 1)
        ]

    def _valid_segments(self, segments):
        return [
            (point_a, point_b)
            for point_a, point_b in segments
            if point_a is not None and point_b is not None
        ]

    def _segment_tuple(self, value):
        try:
            items = list(value)
        except TypeError:
            return None

        if len(items) != 2:
            return None

        point_a = self._point_tuple(items[0])
        point_b = self._point_tuple(items[1])
        if point_a is None or point_b is None:
            return None
        return point_a, point_b

    def _point_tuple(self, value):
        try:
            point = tuple(float(coordinate) for coordinate in value)
        except (TypeError, ValueError):
            return None

        if len(point) != 3:
            return None
        if not all(math.isfinite(coordinate) for coordinate in point):
            return None
        return point

    def _to_voxel(self, point, resolution):
        return (
            point[0] / resolution[0],
            point[1] / resolution[1],
            point[2] / resolution[2],
        )

    def _layer_name(self, compartment):
        if compartment == "neurd skeleton":
            return compartment
        return f"neurd {compartment} skeleton"

    def _response_error_text(self, response):
        try:
            payload = response.json()
        except ValueError:
            return response.text[:500] or response.reason
        return payload.get("message") or payload.get("error") or str(payload)[:500]


##### Add new plugins here and also create them in the admin console. #########
# The key corresponds to the name in the Django "NeuroglancerPlugin" model. 
# This means new plugins require re-deployment and care has to be taken when replacing 
# an existing plugin. 
NEUROGLANCER_PLUGINS = {
    "None": None,
    "Test": TestNeuroglancerPlugin,
    "Neurd Skeleton Points": NeurdSkeletonPointsPlugin,
    "Neurd C2 Skeleton Points": NeurdSkeletonPointsPlugin,
}
