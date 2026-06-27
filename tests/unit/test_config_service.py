import pytest
from datetime import datetime, timezone
from models.database import Config

@pytest.mark.asyncio
async def test_get_icp_default(config_service, async_session):
    # Should return default ICP if nothing in DB
    icp = await config_service.get_icp()
    assert icp is not None
    assert hasattr(icp, "industries")
    
    # Check it was persisted
    result = await async_session.get(Config, "icp")
    assert result is not None

@pytest.mark.asyncio
async def test_update_icp(config_service, sample_icp, async_session):
    from models.schemas import ICPCriteria
    await config_service.update_icp(ICPCriteria(**sample_icp))
    
    # Retrieve and verify
    icp = await config_service.get_icp()
    assert icp.min_employees == 50

@pytest.mark.asyncio
async def test_get_personas_default(config_service):
    from models.schemas import PersonaDefinition
    personas = await config_service.get_persona()
    assert isinstance(personas, PersonaDefinition)

@pytest.mark.asyncio
async def test_update_personas(config_service, sample_personas):
    from models.schemas import PersonaDefinition
    await config_service.update_persona(PersonaDefinition(**sample_personas))
    
    personas = await config_service.get_persona()
    assert "CTO" in personas.job_titles
