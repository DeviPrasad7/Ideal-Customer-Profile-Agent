import uuid
from typing import Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.database import Prospect, HITLRequest, ProcessedEvent
from models.schemas import ProspectSummary

class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_event_been_processed(self, event_hash: str) -> bool:
        result = await self.session.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_hash == event_hash)
        )
        return result.scalar_one_or_none() is not None

    async def mark_event_processed(self, event_hash: str, prospect_id: str) -> None:
        event = ProcessedEvent(event_hash=event_hash, prospect_id=prospect_id)
        self.session.add(event)
        await self.session.commit()

    async def save_prospect_state(self, state: Any) -> None:
        prospect_id_str = state.get("prospect_id")
        if not prospect_id_str:
            return
            
        prospect_id = uuid.UUID(prospect_id_str)
        status = state.get("overall_status", "PENDING")
        
        result = await self.session.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        
        if prospect:
            prospect.state_json = state
            prospect.status = status
            prospect.workflow_thread_id = prospect_id_str
        else:
            prospect = Prospect(
                id=prospect_id,
                company_name=state.get("data", {}).get("company_name", "Unknown"),
                status=status,
                state_json=state,
                workflow_thread_id=prospect_id_str
            )
            self.session.add(prospect)
            
        await self.session.commit()

    async def load_prospect_state(self, prospect_id: str) -> Optional[Any]:
        try:
            pid = uuid.UUID(prospect_id)
        except ValueError:
            return None
            
        result = await self.session.execute(
            select(Prospect).where(Prospect.id == pid)
        )
        prospect = result.scalar_one_or_none()
        return prospect.state_json if prospect else None

    async def rollback_prospect_state(self, prospect_id: str) -> None:
        try:
            pid = uuid.UUID(prospect_id)
        except ValueError:
            return
            
        result = await self.session.execute(
            select(Prospect).where(Prospect.id == pid)
        )
        prospect = result.scalar_one_or_none()
        if prospect:
            prospect.status = "FAILED"
            await self.session.commit()

    async def save_emergency_state(self, state: Any) -> None:
        await self.save_prospect_state(state)

    async def list_prospects(self, filters: dict) -> List[ProspectSummary]:
        query = select(Prospect)
        
        status = filters.get("status")
        if status:
            query = query.where(Prospect.status == status)
            
        company_name = filters.get("company_name")
        if company_name:
            query = query.where(Prospect.company_name.ilike(f"%{company_name}%"))
            
        limit = filters.get("limit", 100)
        offset = filters.get("offset", 0)
        
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        prospects = result.scalars().all()
        
        return [
            ProspectSummary(
                id=p.id,
                company_name=p.company_name,
                status=p.status,
                updated_at=p.updated_at
            ) for p in prospects
        ]

    async def get_prospect(self, prospect_id: str) -> Optional[Prospect]:
        try:
            pid = uuid.UUID(prospect_id)
        except ValueError:
            return None
            
        result = await self.session.execute(
            select(Prospect).where(Prospect.id == pid)
        )
        return result.scalar_one_or_none()

    async def update_prospect_status(self, prospect_id: str, status: str) -> None:
        try:
            pid = uuid.UUID(prospect_id)
        except ValueError:
            return
            
        result = await self.session.execute(
            select(Prospect).where(Prospect.id == pid)
        )
        prospect = result.scalar_one_or_none()
        if prospect:
            prospect.status = status
            await self.session.commit()

    async def create_hitl_request(self, prospect_id: str, summary: str) -> uuid.UUID:
        try:
            pid = uuid.UUID(prospect_id)
        except ValueError:
            raise ValueError("Invalid prospect ID")
            
        hitl = HITLRequest(
            prospect_id=pid,
            summary=summary
        )
        self.session.add(hitl)
        await self.session.commit()
        return hitl.id

    async def get_pending_hitl_requests(self) -> List[HITLRequest]:
        result = await self.session.execute(
            select(HITLRequest).where(HITLRequest.decision == None)
        )
        return list(result.scalars().all())

    async def resolve_hitl_request(self, request_id: uuid.UUID, decision: str, corrections: Optional[dict]) -> None:
        import datetime
        
        result = await self.session.execute(
            select(HITLRequest).where(HITLRequest.id == request_id)
        )
        hitl = result.scalar_one_or_none()
        if hitl:
            hitl.decision = decision
            hitl.corrections = corrections
            hitl.resolved_at = datetime.datetime.now(datetime.timezone.utc)
            await self.session.commit()
