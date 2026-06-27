# Project Tracker – Agentic SaaS Platform for B2B Open Source SaaS Customer Discovery

## Project Overview
- **Goal**: Build a reusable Agentic AI Platform that orchestrates specialised agents to identify and qualify B2B prospects from open source SaaS companies.
- **Use Case**: Monitor web triggers, identify ICP companies, enrich data, find decision-makers, enrich contacts, generate summary, and get HITL approval.
- **Hackathon**: [Insert hackathon name/dates]

## Fundamentals (Must-Have Requirements)
- [x] Agentic Orchestration Engine (Planner-based dynamic routing)
- [x] Specialised Agent Pool (monitor, score, tech stack, enricher, competitor, cross-validator, summarizer, HITL, output dispatcher)
- [x] Reusable Agent/Tool Interface (IAgent, IToolbox)
- [x] Shared Contextual Memory (initial in-memory, now migrating to DB)
- [ ] Configurable Trigger Monitoring (phase-2)
- [ ] ICP Identification (configurable)
- [ ] Validation & Enrichment (partially done)
- [ ] Persona-Based Decision-Maker Discovery (new agents pending)
- [ ] Contact Enrichment (new agents pending)
- [ ] Actionable Summary Generation (done)
- [ ] HITL Approval Gate (integrated via interrupt)
- [ ] User-Editable Business Rules (phase-1 config service)
- [ ] Pluggable Agent Framework (done via IAgent)
- [ ] Intuitive UI (backend only – API provides)

## Current Status (End of Phase-1)
- **Database**: SQLite with SQLAlchemy models defined: `Prospect`, `HITLRequest`, `Config`, `TriggerSource`, `ProcessedEvent`. Database schema initialized and connected.
- **Configuration Service**: `ConfigService` implemented with CRUD for ICP, personas, thresholds. Default values loaded from YAML (`default_icp.yaml`).
- **Memory Service**: `MemoryService` implemented, backing the `IMemoryStore` interface with the database.
- **Checkpointer**: Migrated LangGraph checkpointer from in-memory `MemorySaver` to `SqliteSaver` (using `checkpoints.db`).
- **API (FastAPI)**: Routes created for `/api/config`, `/api/prospects`, `/api/hitl`, and `/api/triggers`.
- **Workflow Wrapper**: `WorkflowService` added to wrap LangGraph engine invocation asynchronously.
- **Phase-1 is COMPLETED**. Application can be run via `python app.py` (Uvicorn).

## Pending for Phase-2
- Implement `PersonaMatcherAgent` and `ContactFinderAgent`.
- Implement `TriggerMonitor` background service (poll RSS, NewsAPI, job boards).
- Implement HITL approval endpoints (POST /approve, /reject) that resume workflow via interrupt.
- Implement `ProspectService` to handle manual submission and retries.
- Add webhook support for output dispatcher.

## Decisions & Trade-offs
- Using SQLite for simplicity; will be replaced with PostgreSQL in production.
- Using `SqliteSaver` separate from app DB to avoid conflicts.
- Default ICP/persona loaded from YAML; config stored in DB for runtime changes.
- All external APIs (Hunter, Clearbit, etc.) will be integrated in phase-2 with circuit breaker.

## Key Files & Structure
- `src/models/` – database and schemas.
- `src/services/` – business logic.
- `src/api/` – FastAPI routers.
- `src/agent/` – existing LangGraph core (untouched except checkpointer).

## Next Actions
1. Implement missing agents.
2. Implement TriggerMonitor.
3. Implement HITL resume logic.
4. Test end-to-end.

---

*Last updated: June 27, 2026*
