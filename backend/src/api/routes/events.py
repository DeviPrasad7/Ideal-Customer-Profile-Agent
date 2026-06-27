from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("")
async def get_events(request: Request):
    """
    Return the last 50 events from the toolbox event store.
    """
    if hasattr(request.app.state, 'toolbox') and hasattr(request.app.state.toolbox, 'event_store'):
        events = request.app.state.toolbox.event_store[-50:]
        # Reverse to show newest first, though the frontend can also do this.
        return {"events": list(reversed(events))}
    return {"events": []}
