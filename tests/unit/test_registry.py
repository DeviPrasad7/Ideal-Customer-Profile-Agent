import pytest
from agent.registry import AgentRegistry
from agent.base import AgentNode

def test_registry_registration():
    registry = AgentRegistry()
    
    class TestAgent(AgentNode):
        pass
        
    registry.register(TestAgent, "test_agent", "Test desc")
        
    assert "test_agent" in registry.list_agents()
    
    agent_class = registry.get_agent("test_agent")
    assert agent_class == TestAgent

def test_global_registry_populated():
    # Test that the global registry has the expected agents
    from agent.registry import registry
    
    agents = registry.list_agents()
    assert "score_node" in agents
    assert "enricher_node" in agents
    assert "hitl_gateway_node" in agents
    assert "summarizer_node" in agents
