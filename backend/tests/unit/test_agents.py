import pytest
from unittest.mock import AsyncMock, patch
from agent.state import GraphState
from agent.agents.enricher import EnricherNode
from agent.agents.score import ScoreNode
from agent.agents.hitl_gateway import HitlGatewayNode
from agent.agents.summarizer import SummarizerNode

@pytest.fixture
def base_state():
    return GraphState(
        prospect_id="123",
        current_trigger_event="",
        config={},
        data={
            "company_name": "TestCorp",
            "website": "testcorp.com"
        },
        validation_notes=[],
        confidence_score=0.0,
        overall_status="PENDING",
        human_override_payload=None,
        executed_agents=[],
        errors=[],
        retry_counts={},
        has_conflict=False,
        tech_detection_status="",
        next_node=""
    )

@pytest.mark.asyncio
async def test_enrichment_agent(mock_toolbox, base_state):
    agent = EnricherNode(mock_toolbox, memory=None, config={})
    
    new_state = await agent(base_state)
    
    # Enrichment should update company info
    assert "firmographics" in new_state["data"]
    assert new_state["data"]["firmographics"]["industries"] == ["B2B SaaS"]
    assert new_state["data"]["firmographics"]["employeeCount"] == 100
    assert "enricher_node" in new_state["executed_agents"]
    
    mock_toolbox.fetch_crunchbase.assert_called_once_with("TestCorp")

@pytest.mark.asyncio
async def test_enrichment_agent_error(mock_toolbox, base_state):
    # Make it throw an error
    mock_toolbox.fetch_crunchbase.side_effect = Exception("API error")
    
    agent = EnricherNode(mock_toolbox, memory=None, config={})
    new_state = await agent(base_state)
    
    assert len(new_state["errors"]) == 1
    assert "API error" in new_state["errors"][0]

@pytest.mark.asyncio
async def test_scoring_agent(mock_toolbox, base_state):
    base_state["data"]["raw_signals"] = ["signal1", "signal2"]
    agent = ScoreNode(mock_toolbox, memory=None, config={"icp": {}})
    
    new_state = await agent(base_state)
    
    assert "score_node" in new_state["executed_agents"]
    assert "scored_signals" in new_state["data"]
    assert len(new_state["data"]["scored_signals"]) == 2

@pytest.mark.asyncio
async def test_hitl_gateway_agent(mock_toolbox, base_state):
    # Set up condition where HITL is required (missing website)
    base_state["data"]["website"] = ""
    
    agent = HitlGatewayNode(mock_toolbox, memory=None, config={})
    
    with patch("agent.agents.hitl_gateway.interrupt") as mock_interrupt:
        mock_interrupt.return_value = {"action": "APPROVED", "edits": {"score": 90}}
        new_state = await agent(base_state)
        
        mock_interrupt.assert_called_once()
        assert new_state["overall_status"] == "APPROVED"
        assert new_state["data"]["score"] == 90

@pytest.mark.asyncio
async def test_summary_agent(mock_toolbox, base_state):
    agent = SummarizerNode(mock_toolbox, memory=None, config={})
    
    new_state = await agent(base_state)
    
    assert "summarizer_node" in new_state["executed_agents"]
    assert "summary_object" in new_state["data"]
    mock_toolbox.generate_text.assert_called_once()
