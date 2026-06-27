from typing import Dict, List, Type, Callable, Any

from .base import AgentNode


class AgentRegistry:
    """Registry for managing and discovering agent nodes."""

    def __init__(self):
        self._agents: Dict[str, Type[AgentNode]] = {}
        self._descriptions: Dict[str, str] = {}

    def register(self, cls: Type[AgentNode], name: str, description: str = "") -> None:
        """Register an agent class with the given name and description."""
        if name in self._agents:
            raise ValueError(f"Agent with name '{name}' is already registered.")
        
        self._agents[name] = cls
        self._descriptions[name] = description

    def get_agent(self, name: str) -> Type[AgentNode]:
        """Retrieve an agent class by name."""
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in registry.")
        return self._agents[name]

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def list_agents_with_descriptions(self) -> List[dict]:
        """Return agent metadata dicts for LLM prompt construction.

        Returns:
            [{"name": "score_node", "description": "Scores the prospect..."}, ...]
        """
        return [
            {"name": name, "description": self._descriptions.get(name, "")}
            for name in self._agents.keys()
        ]

    def get_description(self, name: str) -> str:
        """Retrieve the description for a registered agent."""
        return self._descriptions.get(name, "")


# Singleton registry instance
registry = AgentRegistry()

def register_agent(name: str, description: str = "") -> Callable[[Type[AgentNode]], Type[AgentNode]]:
    """
    Decorator to register an agent class with the global registry.
    
    Args:
        name (str): The name used to refer to this agent in the workflow.
        description (str): A description of the agent's purpose, used by the planner.
    """
    def wrapper(cls: Type[AgentNode]) -> Type[AgentNode]:
        registry.register(cls, name, description)
        return cls
    return wrapper
