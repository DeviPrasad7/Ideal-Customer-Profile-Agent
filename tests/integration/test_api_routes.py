import pytest
import uuid
from httpx import AsyncClient
from models.database import Prospect, Config, HITLRequest
from models.schemas import ICPCriteria

@pytest.mark.asyncio
async def test_get_icp_route(app_client: AsyncClient, config_service):
    # Set default
    icp = ICPCriteria(industries=["B2B"], min_revenue=100, max_revenue=1000, min_employees=10, max_employees=50, locations=["NA"], tech_stack=[], behaviors=[])
    await config_service.update_icp(icp)
    
    response = await app_client.get("/api/config/icp")
    assert response.status_code == 200
    assert response.json()["industries"] == ["B2B"]

@pytest.mark.asyncio
async def test_update_icp_route(app_client: AsyncClient, sample_icp):
    response = await app_client.put("/api/config/icp", json=sample_icp)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_start_workflow_route(app_client: AsyncClient, sample_company_data):
    response = await app_client.post("/api/prospects", json={
        "company_name": sample_company_data["company_name"],
        "website": sample_company_data["website"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prospect_id" in data

@pytest.mark.asyncio
async def test_get_pending_hitl_route(app_client: AsyncClient, hitl_service, memory_service, sample_company_data):
    # Create prospect
    pid = str(uuid.uuid4())
    await memory_service.save_prospect_state({
        "prospect_id": pid, "overall_status": "PENDING", "data": {"company_name": sample_company_data["company_name"]}
    })
    
    # Create hitl request
    req = await hitl_service.create_request(pid, {"reason": "Please approve"})
    
    response = await app_client.get("/api/hitl/pending")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["id"] == str(req)

@pytest.mark.asyncio
async def test_approve_hitl_route(app_client: AsyncClient, hitl_service, memory_service, sample_company_data, mocker):
    # Mock WorkflowService.resume_with_hitl since API calls it
    mocker.patch("services.workflow_service.WorkflowService.resume_with_hitl")
    
    pid = str(uuid.uuid4())
    await memory_service.save_prospect_state({
        "prospect_id": pid, "overall_status": "PENDING", "data": {"company_name": "HITL Corp"}
    })
    req = await hitl_service.create_request(pid, {"reason": "Please approve"})
    
    response = await app_client.post(f"/api/hitl/{req}/approve", json={"corrections": {"score": 95}})
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
