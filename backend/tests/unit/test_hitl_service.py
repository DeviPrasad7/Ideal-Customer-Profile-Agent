import pytest
import uuid
from models.database import Prospect, HITLRequest

@pytest.fixture
async def sample_prospect(async_session):
    p = Prospect(company_name="HITL Corp", status="PENDING_HUMAN")
    async_session.add(p)
    await async_session.commit()
    await async_session.refresh(p)
    return p

@pytest.mark.asyncio
async def test_create_hitl_request(hitl_service, sample_prospect, async_session):
    req_id = await hitl_service.create_request(str(sample_prospect.id), {"reason": "Please review this company"})
    
    # Verify in DB
    result = await async_session.get(HITLRequest, req_id)
    assert result is not None
    assert result.prospect_id == sample_prospect.id
    assert result.summary == "Please review this company"
    assert result.decision is None

@pytest.mark.asyncio
async def test_get_pending_requests(hitl_service, sample_prospect, memory_service):
    await hitl_service.create_request(str(sample_prospect.id), {"reason": "Pending 1"})
    
    req2_id = await hitl_service.create_request(str(sample_prospect.id), {"reason": "Pending 2"})
    await hitl_service.resolve_request(str(req2_id), "APPROVE", {})
    
    pending = await memory_service.get_pending_hitl_requests()
    assert len(pending) == 1
    assert pending[0].summary == "Pending 1"

@pytest.mark.asyncio
async def test_approve_request(hitl_service, sample_prospect, async_session):
    req_id = await hitl_service.create_request(str(sample_prospect.id), {"reason": "To Approve"})
    
    await hitl_service.resolve_request(str(req_id), "APPROVE", {"score": 90})
    
    resolved = await async_session.get(HITLRequest, req_id)
    assert resolved.decision == "APPROVE"
    assert resolved.corrections == {"score": 90}
    assert resolved.resolved_at is not None
    
    assert resolved.resolved_at is not None

@pytest.mark.asyncio
async def test_reject_request(hitl_service, sample_prospect, async_session):
    req_id = await hitl_service.create_request(str(sample_prospect.id), {"reason": "To Reject"})
    
    await hitl_service.resolve_request(str(req_id), "REJECT", {"reason": "Not a fit"})
    
    resolved = await async_session.get(HITLRequest, req_id)
    assert resolved.decision == "REJECT"
    
    assert resolved.decision == "REJECT"
