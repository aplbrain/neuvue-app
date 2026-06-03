from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import copy
import requests
from django.conf import settings
from urllib.parse import quote


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
    Adds a public NEURD precomputed skeleton source to the current segmentation
    layer. The skeleton service serves coordinates in nanometers and exposes a
    per-vertex compartment attribute for shader-based coloring.
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.dataset_schema = params.get("dataset_schema")
        self.base_url = settings.NEURD_LAMBDA_URL
        self.request_timeout = params.get("request_timeout", 30)
        self.target_layer_name = params.get("target_layer_name")
        self.created_layer_name = params.get("layer_name", "neurd skeleton")
        self.compartment_colors = {
            **DEFAULT_COMPARTMENT_COLORS,
            **params.get("compartment_colors", {}),
        }

    def modify_state(self, state: Dict[str, Any], **kwargs) -> PluginOutput:
        dataset_schema = self.dataset_schema

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

        if not settings.NEURD_LAMBDA_URL:
            return PluginOutput(
                modified_state=state,
                status_code=500,
                message="NEURD skeleton plugin is not configured: NEURD_LAMBDA_URL is empty.",
                additional_info={},
            )

        seg_ids = self._segment_ids(kwargs.get("plugin_inputs"))
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

        skeleton_source = self._skeleton_source(dataset_schema)

        for seg_id in seg_ids:
            validation = self._validate_skeleton(
                state,
                dataset_schema,
                seg_id,
            )
            if validation is not None:
                return validation

        try:
            modified_state = copy.deepcopy(state)
            layer = self._segmentation_layer(modified_state, kwargs.get("datastack"))
            if layer is None:
                return PluginOutput(
                    modified_state=state,
                    status_code=400,
                    message=(
                        "NEURD skeleton plugin could not find or create a "
                        "segmentation layer for the skeleton source."
                    ),
                    additional_info={"dataset_schema": dataset_schema},
                )

            self._apply_skeleton_source(layer, skeleton_source, seg_ids)
        except Exception as e:
            return PluginOutput(
                modified_state=state,
                status_code=500,
                message=f"NEURD skeleton plugin could not update the Neuroglancer state: {e}",
                additional_info={
                    "dataset_schema": dataset_schema,
                    "selected_segments": seg_ids,
                    "skeleton_source": skeleton_source,
                },
            )

        return PluginOutput(
            modified_state=self._state_for_restore(modified_state),
            status_code=200,
            message="NEURD skeleton source added.",
            additional_info={
                "dataset_schema": dataset_schema,
                "selected_segments": seg_ids,
                "skeleton_source": skeleton_source,
            },
        )

    def _validate_skeleton(self, state, dataset_schema, seg_id):
        request_url = (
            f"{self.base_url.rstrip('/')}/precomputed/skeletons/"
            f"{quote(str(dataset_schema), safe='')}/"
            "validate/"
            f"{quote(str(seg_id), safe='')}"
        )
        try:
            response = requests.get(request_url, timeout=self.request_timeout)
            response.raise_for_status()
        except requests.Timeout:
            return PluginOutput(
                modified_state=state,
                status_code=504,
                message=(
                    f"NEURD skeleton validation timed out for segment {seg_id} "
                    f"after {self.request_timeout} seconds."
                ),
                additional_info={
                    "dataset_schema": dataset_schema,
                    "request_url": request_url,
                },
            )
        except requests.HTTPError:
            return PluginOutput(
                modified_state=state,
                status_code=response.status_code,
                message=(
                    f"NEURD skeleton validation failed for segment {seg_id} "
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
        return None

    def _skeleton_source(self, dataset_schema):
        return (
            f"precomputed://{self.base_url.rstrip('/')}/precomputed/skeletons/"
            f"{quote(str(dataset_schema), safe='')}"
        )

    def _state_for_restore(self, state):
        state = copy.deepcopy(state)
        state.pop("layout", None)
        return state

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
                if str(segment_id).strip() and "!" not in str(segment_id)
            ]
        return [
            segment_id
            for segment_id in str(raw_segment_ids)
            .replace(",", " ")
            .split()
            if segment_id and "!" not in segment_id
        ]

    def _segmentation_layer(self, state, datastack):
        layers = state.setdefault("layers", [])
        layer = self._find_segmentation_layer(layers)
        if layer is not None:
            return layer

        segmentation_source = self.params.get("segmentation_source")
        if not segmentation_source and datastack is not None:
            segmentation_source = getattr(datastack, "segmentation_source", None)

        if not segmentation_source:
            return None

        layer = {
            "type": "segmentation",
            "name": self.created_layer_name,
            "source": segmentation_source,
            "segments": [],
        }
        layers.append(layer)
        return layer

    def _find_segmentation_layer(self, layers):
        if self.target_layer_name:
            for layer in layers:
                if (
                    self._is_segmentation_layer(layer)
                    and layer.get("name") == self.target_layer_name
                ):
                    return layer

        for layer in layers:
            if self._is_segmentation_layer(layer):
                return layer
        return None

    def _is_segmentation_layer(self, layer):
        return "segmentation" in str(layer.get("type", ""))

    def _apply_skeleton_source(self, layer, skeleton_source, seg_ids):
        layer["skeletons"] = skeleton_source
        layer["skeletonShader"] = self._skeleton_shader()
        layer.setdefault("skeletonRendering", {})
        layer["skeletonRendering"].update(
            {
                "lineWidth2d": self.params.get("line_width_2d", 3),
                "lineWidth3d": self.params.get("line_width_3d", 2),
            }
        )

        segments = layer.get("segments", [])
        if not isinstance(segments, list):
            segments = []
        segment_set = {str(segment) for segment in segments}
        for seg_id in seg_ids:
            segment = str(seg_id)
            if segment not in segment_set:
                segments.append(segment)
                segment_set.add(segment)
        layer["segments"] = segments

        hidden_segments = layer.get("hiddenSegments")
        if isinstance(hidden_segments, list):
            layer["hiddenSegments"] = [
                segment
                for segment in hidden_segments
                if str(segment) not in segment_set
            ]

    def _skeleton_shader(self):
        branches = []
        for index, compartment in enumerate(DEFAULT_COMPARTMENT_COLORS, start=1):
            color = self._hex_color_to_vec3(
                self.compartment_colors.get(compartment, "#ffffff")
            )
            prefix = "if" if index == 1 else "else if"
            branches.append(
                f"  {prefix} (compartment < {index + 0.5:.1f}) {{ "
                f"emitRGB(vec3({color})); return; }}"
            )

        return "\n".join(
            [
                "void main() {",
                "  float compartment = prop_compartment();",
                *branches,
                "  emitDefault();",
                "}",
            ]
        )

    def _hex_color_to_vec3(self, color):
        color = str(color).strip()
        if color.startswith("#"):
            color = color[1:]
        if len(color) != 6:
            color = "ffffff"
        try:
            channels = [
                int(color[index:index + 2], 16) / 255.0
                for index in (0, 2, 4)
            ]
        except ValueError:
            channels = [1.0, 1.0, 1.0]
        return ", ".join(f"{channel:.6f}" for channel in channels)

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
    "NEURD Skeletons": NeurdSkeletonPointsPlugin
}
