import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from agent.state import GraphState
from agent.agents.dynamic_planner import DynamicPlannerNode

@pytest.mark.asyncio
async def test_dynamic_planner_simulate_failure():
    # Setup mocks
    toolbox = Mock()
    memory = Mock()
    config = {}
    registry = Mock()
    
    registry.list_agents_with_descriptions.return_value = [
        {"name": "enricher_node", "description": "Enricher"}
    ]
    
    node = DynamicPlannerNode(toolbox, memory, config, registry)
    
    # Initial state with simulate_failure True
    state: GraphState = {
        "prospect_id": "123",
        "current_trigger_event": "test",
        "config": {},
        "data": {"company_name": "Test Corp"},
        "validation_notes": [],
        "confidence_score": 0.0,
        "overall_status": "PENDING",
        "human_override_payload": None,
        "executed_agents": ["monitor_node", "enricher_node"],
        "errors": [],
        "retry_counts": {},
        "has_conflict": False,
        "tech_detection_status": "PENDING",
        "next_node": "",
        "last_agent": "enricher_node",
        "simulate_failure": True
    }
    
    # 1. First execution should simulate failure and force retry
    result1 = await node(state)
    assert result1["next_node"] == "enricher_node"
    assert result1["retry_counts"]["enricher_node"] == 1
    
    # 2. Second execution (with retry_count=1) should still force retry since < 2
    state["retry_counts"] = {"enricher_node": 1}
    result2 = await node(state)
    assert result2["next_node"] == "enricher_node"
    assert result2["retry_counts"]["enricher_node"] == 1 # This will add up in the reducer to 2
    
    # 3. Third execution (with retry_count=2) should proceed normally via LLM
    state["retry_counts"] = {"enricher_node": 2}
    
    # Mock LLM to return next node
    toolbox.generate_text = AsyncMock(return_value='{"next_node": "__end__", "reasoning": "Done"}')
    
    result3 = await node(state)
    assert result3["next_node"] == "__end__"
    assert "retry_counts" not in result3
