import asyncio
from agent.graph import app
from agent.state import GraphState
import structlog

logger = structlog.get_logger()

class WorkflowService:
    """Wrapper to run the LangGraph workflow."""
    
    @staticmethod
    async def submit_prospect(state: GraphState, thread_id: str):
        """
        Submits a prospect state to the LangGraph workflow asynchronously.
        """
        async def run_workflow():
            logger.info("Starting workflow for prospect", thread_id=thread_id)
            config = {"configurable": {"thread_id": thread_id}}
            try:
                # In LangGraph 0.2.x, ainvoke is used for async execution
                final_state = await app.ainvoke(state, config=config)
                logger.info("Workflow completed", thread_id=thread_id, final_status=final_state.get("overall_status"))
            except Exception as e:
                logger.error("Workflow failed", thread_id=thread_id, error=str(e))

        asyncio.create_task(run_workflow())
        return thread_id
