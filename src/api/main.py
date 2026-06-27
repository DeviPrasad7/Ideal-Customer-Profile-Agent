from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import config, prospects, hitl, triggers, events
from services.trigger_monitor import TriggerMonitor
from agent.graph import get_app
from agent.utils import Toolbox
from services.memory_service import MemoryService
from models.database import async_session, init_db
from core.settings import settings
from services.config_service import ConfigService
from core.logging import setup_logging
from services.hitl_service import HITLService

# Initialize logging at startup
setup_logging(settings.LOG_LEVEL)

# Global trigger monitor instance removed (moved to state)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables (safe to call every startup)
    if settings.APP_ENV != "test":
        await init_db()

    # Initialize LangGraph workflow dependencies
    from services.llm_service import LLMService
    from services.scraping_service import ScrapingService
    from services.enrichment_service import EnrichmentService
    
    toolbox = Toolbox(
        llm_service=LLMService(),
        scraping_service=ScrapingService(),
        enrichment_service=EnrichmentService()
    )
    
    memory_service = MemoryService(async_session)
    
    async with async_session() as session:
        config_service = ConfigService(session)
        
        # Create configuration dictionary to pass to agents
        config_dict = {
            "icp": await config_service.get_icp(),
            "personas": await config_service.get_persona()
        }
    
    graph_app = await get_app(toolbox, memory_service, config_dict)
    app.state.graph_app = graph_app
    app.state.hitl_service = HITLService(memory_service)
    
    # Instantiate TriggerMonitor and auto-start background polling
    app.state.trigger_monitor = TriggerMonitor(toolbox)
    app.state.trigger_monitor.start()

    # Make toolbox accessible to endpoints (e.g. events)
    app.state.toolbox = toolbox

    # Insert Magic Seed Prospect if empty
    existing_prospects = await memory_service.list_prospects({"limit": 1})
    if not existing_prospects:
        import uuid
        magic_id = str(uuid.uuid4())
        magic_state = {
            "prospect_id": magic_id,
            "current_trigger_event": "manual_submission",
            "data": {
                "company_name": "Streamlit",
                "website_url": "https://streamlit.io",
                "firmographics": {
                    "tech_stack": [
                        {"technology": "Python", "category": "Language", "confidence": 0.99, "source": "magic_seed"},
                        {"technology": "React", "category": "Frontend", "confidence": 0.99, "source": "magic_seed"},
                        {"technology": "TypeScript", "category": "Language", "confidence": 0.99, "source": "magic_seed"}
                    ]
                }
            },
            "validation_notes": [],
            "confidence_score": 0.0,
            "overall_status": "PENDING",
            "human_override_payload": None,
            "executed_agents": ["enricher_node"],
            "errors": [],
            "has_conflict": False,
            "tech_detection_status": "PENDING",
            "simulate_failure": False
        }
        await memory_service.save_prospect_state(magic_state)
        # We don't submit to workflow immediately to let the demo run when started, 
        # or we just leave it in PENDING. Let's submit to workflow to process the rest of the nodes!
        from services.workflow_service import WorkflowService
        # Actually wait, maybe we don't submit right here because workflow_service is instantiated later.
        # So we just leave it in the DB, and the frontend can show it or it can be triggered later. 
        # But wait, to demo dynamic planner skipping, it needs to run.
        # Let's run it after instantiating workflow_service!

    # Inject graph_app into WorkflowService – instance sets class-level refs
    # so legacy WorkflowService.submit_prospect() calls continue to work.
    from services.workflow_service import WorkflowService
    app.state.workflow_service = WorkflowService(graph_app, app.state.hitl_service)

    # Now that workflow_service is available, if we inserted the magic seed, trigger it!
    if not existing_prospects:
        await WorkflowService.submit_prospect(magic_state, thread_id=magic_id)

    yield

app = FastAPI(title="ICP Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(prospects.router)
app.include_router(hitl.router)
app.include_router(triggers.router)
app.include_router(events.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
