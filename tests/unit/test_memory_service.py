import pytest
import uuid
from models.database import Prospect

@pytest.mark.asyncio
async def test_save_prospect_state(memory_service, sample_company_data):
    pid = str(uuid.uuid4())
    state = {
        "prospect_id": pid,
        "overall_status": "PENDING",
        "data": {"company_name": sample_company_data["company_name"]}
    }
    await memory_service.save_prospect_state(state)
    
    prospect = await memory_service.get_prospect(pid)
    assert prospect is not None
    assert prospect.company_name == sample_company_data["company_name"]
    assert prospect.status == "PENDING"

@pytest.mark.asyncio
async def test_list_prospects(memory_service, sample_company_data):
    pid1 = str(uuid.uuid4())
    pid2 = str(uuid.uuid4())
    
    await memory_service.save_prospect_state({
        "prospect_id": pid1, "overall_status": "PENDING", "data": {"company_name": "Company A"}
    })
    await memory_service.save_prospect_state({
        "prospect_id": pid2, "overall_status": "QUALIFIED", "data": {"company_name": "Company B"}
    })
    
    # Get pending
    pending = await memory_service.list_prospects({"status": "PENDING"})
    assert len(pending) == 1
    assert pending[0].company_name == "Company A"
    
    # Get all
    all_prospects = await memory_service.list_prospects({})
    assert len(all_prospects) >= 2

@pytest.mark.asyncio
async def test_update_prospect_status(memory_service, sample_company_data):
    pid = str(uuid.uuid4())
    await memory_service.save_prospect_state({
        "prospect_id": pid, "overall_status": "PENDING", "data": {"company_name": "Test"}
    })
    
    await memory_service.update_prospect_status(pid, "REJECTED")
    prospect = await memory_service.get_prospect(pid)
    assert prospect.status == "REJECTED"

@pytest.mark.asyncio
async def test_deduplication(memory_service, sample_company_data):
    pid = str(uuid.uuid4())
    state = {
        "prospect_id": pid, "overall_status": "PENDING", "data": {"company_name": "Test"}
    }
    
    await memory_service.save_prospect_state(state)
    await memory_service.save_prospect_state(state)
    
    prospect = await memory_service.get_prospect(pid)
    assert prospect is not None
