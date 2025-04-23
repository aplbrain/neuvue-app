import abc
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

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

#                           Add new plugins here
# The key corresponds to the name in the Django "NeuroglancerPlugin" model. 
# This means new plugins require re-deployment and care has to be taken when replacing 
# an existing plugin. 
NEUROGLANCER_PLUGINS = {
    "None": None,
    "Test": TestNeuroglancerPlugin
}