from typing import Any, Dict, Protocol, TypedDict

from .state import GraphState


class AgentConfig(TypedDict, total=False):
    """Configuration passed to agents."""
    icp: Dict[str, Any]
    personas: Dict[str, Any]
    # Add other config fields as needed


class AgentNode(Protocol):
    """Formal interface for all agents in the platform."""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        Execute the agent's core logic.
        
        Args:
            state (GraphState): The current state of the workflow.
            
        Returns:
            Dict[str, Any]: The updates to apply to the state.
        """
        ...
