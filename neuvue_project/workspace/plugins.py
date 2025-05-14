from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
import requests
from django.conf import settings
from nglui.statebuilder import StateBuilder, AnnotationLayerConfig, PointMapper, site_utils
import json
import pandas as pd

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

    def modify_state(self, state: Dict[str, Any]) -> PluginOutput:
        # For testing, we just return the original state in a slightly modified position
        offset =  self.params.get("offset", 0)
        state['position'] = [state['position'][0]+offset, state['position'][1]+offset, state['position'][2]+offset]
        return PluginOutput(
            modified_state=state,
            status_code=200,
            message="Plugin executed successfully.",
            additional_info={"test": "This is a test plugin."}
        )

class NeurdC2SkeletonPointsPlugin(NeuroglancerPlugin):
    """
    This plugin queries NEURD for the skeletons of all C2 seg IDs listed and
    adds them to the ng state as a new annotation layer.
    """
    def __init__(self, **params):
        super().__init__(**params)
        self.resolution = [8,8,33]
        self.seg_layer = "precomputed://gs://h01-release/data/20210601/c2"
        self.base_url = settings.NEURD_LAMBDA_URL

    def modify_state(self, state: Dict[str, Any]) -> PluginOutput:

        # Get seg ids to query
        seg_ids = []
        for layer in state["layers"]:
            if layer["source"] == self.seg_layer:
                seg_ids = layer["segments"]
        position = state["position"]

        # Query for skeleton
        skel_list = []
        for seg_id in seg_ids:
            if '!' not in seg_id:
                request_url = f"{self.base_url}/skeleton/{seg_id}"
                try:
                    response = requests.get(request_url)
                    # Raise exception if request is unsuccessful
                    response.raise_for_status()
                    # Process the successful response
                    skel_list.extend(json.loads(response.text)["skeleton_points"])
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    return PluginOutput(
                        modified_state=state,
                        status_code=500,
                        message=f"An unexpected error occurred: {e}",
                        additional_info={}
                    )
        
        # Process the skeleton points, converting them from nm to voxels
        points_list_vx = []
        RESOLUTION = self.resolution
        for line_segment in skel_list:
            for point in line_segment:
                points_list_vx.append([point[0]/RESOLUTION[0], point[1]/RESOLUTION[1], point[2]/RESOLUTION[2]])
        points_list_vx = [list(t) for t in dict.fromkeys(tuple(sub) for sub in points_list_vx)]
        points_df = pd.DataFrame({"points": points_list_vx})
        
        # add to state
        site_utils.set_default_config(target_site='spelunker')
        view_options = {'position': [position[0]*2, position[1]*2, position[2]]}
        points = PointMapper(point_column='points')
        skeleton_layer = AnnotationLayerConfig(name="neurd skeleton", color="white", mapping_rules=points)
        state_builder = StateBuilder([skeleton_layer], base_state=state, view_kws=view_options)
        final_state = state_builder.render_state(points_df, return_as="dict")

        # Return modified state
        return PluginOutput(
            modified_state=final_state,
            status_code=200,
            message="Plugin executed successfully.",
            additional_info={}
        )


##### Add new plugins here and also create them in the admin console. #########
# The key corresponds to the name in the Django "NeuroglancerPlugin" model. 
# This means new plugins require re-deployment and care has to be taken when replacing 
# an existing plugin. 
NEUROGLANCER_PLUGINS = {
    "None": None,
    "Test": TestNeuroglancerPlugin,
    "Neurd C2 Skeleton Points": NeurdC2SkeletonPointsPlugin
}