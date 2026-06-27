import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from agent.agents.planner import PlannerNode
from agent.state import GraphState

@pytest.fixture
def mock_registry():
    registry = MagicMock()
    registry.list_agents.return_value = ["score_node", "enricher_node", "hitl_gateway_node", "output_dispatcher_node"]
    registry.get_description.return_value = "Mock description"
    return registry

@pytest.fixture
def base_planner_state():
    return GraphState(
        prospect_id="123",
        overall_status="PENDING",
        executed_agents=["enricher_node"],
        errors=[],
        retry_counts={},
        data={},
        current_agent="planner_node",
        next_agent="",
        messages=[],
        agent_history=[]
    )

@pytest.mark.asyncio
async def test_planner_llm_routing(mock_toolbox, mock_registry, base_planner_state):
    # Mock LLM to return specific routing
    mock_toolbox.generate_text = AsyncMock(return_value='{"next_node": "score_node", "reasoning": "Need score"}')
    
    planner = PlannerNode(toolbox=mock_toolbox, memory=None, config={}, registry=mock_registry)
    result = await planner(base_planner_state)
    
    assert result["next_node"] == "score_node"
    assert "planner_node" in result["executed_agents"]

@pytest.mark.asyncio
async def test_planner_fallback_routing(mock_toolbox, mock_registry, base_planner_state):
    # Make LLM return invalid JSON
    mock_toolbox.generate_text = AsyncMock(return_value='Invalid response format')
    
    planner = PlannerNode(toolbox=mock_toolbox, memory=None, config={}, registry=mock_registry)
    result = await planner(base_planner_state)
    
    # Fallback should route to score_node if score is missing
    assert result["next_node"] == "score_node"

@pytest.mark.asyncio
async def test_planner_retry_logic(mock_toolbox, mock_registry, base_planner_state):
    # Agent just errored
    base_planner_state["executed_agents"] = ["enricher_node"]
    base_planner_state["errors"] = ["enricher_node: API Failure"]
    base_planner_state["retry_counts"] = {"enricher_node": 1}
    
    planner = PlannerNode(toolbox=mock_toolbox, memory=None, config={"MAX_RETRIES": 3}, registry=mock_registry)
    result = await planner(base_planner_state)
    
    # It should retry the enricher node
    assert result["next_node"] == "enricher_node"
    assert result["retry_counts"]["enricher_node"] == 2

@pytest.mark.asyncio
async def test_planner_max_retries(mock_toolbox, mock_registry, base_planner_state):
    # Agent just errored and reached max retries
    base_planner_state["executed_agents"] = ["enricher_node"]
    base_planner_state["errors"] = ["enricher_node: API Failure"]
    base_planner_state["retry_counts"] = {"enricher_node": 3}
    
    # Mock LLM to return score_node (moving on)
    mock_toolbox.generate_text = AsyncMock(return_value='{"next_node": "score_node"}')
    
    planner = PlannerNode(toolbox=mock_toolbox, memory=None, config={"MAX_RETRIES": 3}, registry=mock_registry)
    result = await planner(base_planner_state)
    
    assert result["next_node"] == "score_node"

@pytest.mark.asyncio
async def test_planner_hitl_approval_routing(mock_toolbox, mock_registry, base_planner_state):
    base_planner_state["overall_status"] = "APPROVED"
    
    planner = PlannerNode(toolbox=mock_toolbox, memory=None, config={}, registry=mock_registry)
    result = await planner(base_planner_state)
    
    assert result["next_node"] == "output_dispatcher_node"
