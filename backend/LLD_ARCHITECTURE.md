<h1 align="center">Low-Level Design Architecture</h1>

<p align="center">
  <strong>Detailed low-level design covering data models, state machine transitions, DTO specifications, schema validation rules, database design, and the architectural contracts that govern every layer of the ICP Agent platform.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Database-7_Tables-4169E1?style=for-the-badge" alt="Tables">
  <img src="https://img.shields.io/badge/DTOs-6_Transfer_Objects-FF6F00?style=for-the-badge" alt="DTOs">
  <img src="https://img.shields.io/badge/Schemas-11_Pydantic_Models-4CAF50?style=for-the-badge" alt="Schemas">
  <img src="https://img.shields.io/badge/State_Machine-5_States-E91E63?style=for-the-badge" alt="States">
  <img src="https://img.shields.io/badge/Reducers-2_Custom_Functions-9C27B0?style=for-the-badge" alt="Reducers">
</p>

---

## Table of Contents

- [Database Design](#database-design)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [State Machine Definitions](#state-machine-definitions)
- [Data Transfer Object Specification](#data-transfer-object-specification)
- [Schema Validation Rules](#schema-validation-rules)
- [GraphState Contract Specification](#graphstate-contract-specification)
- [API Request/Response Contracts](#api-requestresponse-contracts)
- [Configuration Schema Design](#configuration-schema-design)
- [Index Strategy](#index-strategy)
- [Connection Pool Design](#connection-pool-design)

---

## Database Design

### Schema Overview

The database consists of 7 tables designed for the specific needs of an agentic workflow platform:

```mermaid
erDiagram
    prospects ||--o{ hitl_requests : "has many"
    prospects }o--o| workflows : "optionally uses"

    prospects {
        uuid id PK
        string display_id "nullable, indexed"
        string company_name "not null, indexed"
        string website "nullable"
        string status "not null, indexed, default PENDING"
        json state_json "nullable, full agent state"
        datetime created_at "tz-aware, auto"
        datetime updated_at "tz-aware, auto-update"
        string workflow_thread_id "nullable"
        uuid custom_workflow_id FK "nullable, SET NULL"
    }

    hitl_requests {
        uuid id PK
        string display_id "nullable, indexed"
        uuid prospect_id FK "CASCADE"
        string summary "not null"
        string decision "nullable, indexed"
        json corrections "nullable"
        datetime created_at "server_default now()"
        datetime resolved_at "nullable"
    }

    custom_agents {
        uuid id PK
        string name "indexed, not null"
        string description "not null"
        string system_prompt "not null"
        json allowed_tools "nullable"
        datetime created_at "server_default now()"
    }

    workflows {
        uuid id PK
        string name "indexed, not null"
        string description "nullable"
        json steps "not null, DAG definition"
        datetime created_at "server_default now()"
    }

    config {
        string key PK
        json value "not null"
        datetime updated_at "tz-aware, auto-update"
    }

    trigger_sources {
        uuid id PK
        string type "not null"
        string url "nullable"
        integer interval_seconds "default 3600"
        boolean enabled "default true"
        json config "nullable"
        datetime created_at "tz-aware"
    }

    processed_events {
        string event_hash PK
        string prospect_id "not null"
        string status "not null, default completed"
        datetime processed_at "tz-aware"
    }
```

### Table Design Decisions

| Table | Design Decision | Rationale |
|:---|:---|:---|
| `prospects` | `state_json` stores the complete `GraphState` as JSON | Enables full state reconstruction without joining, critical for workflow resume |
| `prospects` | `workflow_thread_id` stored as String | LangGraph thread IDs are opaque strings, not UUIDs |
| `hitl_requests` | `CASCADE` on prospect deletion | HITL requests are meaningless without their parent prospect |
| `workflows` | `steps` stored as JSON | Workflow DAGs are complex nested structures (nodes + edges) not suitable for relational normalization |
| `config` | Key-value store with JSON values | Runtime configuration changes frequently; relational modeling would require schema migrations |
| `processed_events` | `event_hash` as PK | Content-based deduplication -- same event from different poll cycles has the same hash |
| `processed_events` | `status` column with outbox semantics | Enables two-phase commit and orphan cleanup |

---

## Entity Relationship Diagram

```mermaid
graph TB
    subgraph Entities["Domain Entities"]
        P["Prospect"]
        H["HITLRequest"]
        W["Workflow"]
        CA["CustomAgent"]
        C["Config"]
        TS["TriggerSource"]
        PE["ProcessedEvent"]
    end

    subgraph Relationships["Relationships"]
        P -->|"1:N"| H
        P -->|"N:0..1"| W
        TS -->|"generates"| PE
        PE -->|"creates"| P
        CA -->|"executed by"| P
    end

    subgraph Lifecycle["Entity Lifecycle"]
        TS -->|"poll"| PE
        PE -->|"new event"| P
        P -->|"workflow runs"| H
        H -->|"resolved"| P
    end
```

---

## State Machine Definitions

### Prospect Status State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: Prospect created

    PENDING --> IN_PROGRESS: Workflow starts
    IN_PROGRESS --> PENDING_HUMAN: HITL interrupt triggered
    IN_PROGRESS --> COMPLETED: All agents executed
    IN_PROGRESS --> FAILED: Max errors exceeded
    
    PENDING_HUMAN --> APPROVED: Human approves
    PENDING_HUMAN --> REJECTED: Human rejects
    PENDING_HUMAN --> EDITED: Human edits data
    PENDING_HUMAN --> TIMEOUT: Review timeout

    APPROVED --> DISPATCHED: Output dispatcher fires
    EDITED --> IN_PROGRESS: Workflow resumes with edits

    DISPATCHED --> [*]
    REJECTED --> [*]
    TIMEOUT --> [*]
    COMPLETED --> [*]
    FAILED --> [*]
```

| Status | Description | Transitions To |
|:---|:---|:---|
| `PENDING` | Prospect created, waiting for workflow execution | `IN_PROGRESS` |
| `IN_PROGRESS` | Agents are executing | `PENDING_HUMAN`, `COMPLETED`, `FAILED` |
| `PENDING_HUMAN` | Waiting for human review | `APPROVED`, `REJECTED`, `EDITED`, `TIMEOUT` |
| `APPROVED` | Human approved the prospect | `DISPATCHED` |
| `REJECTED` | Human rejected the prospect | Terminal |
| `EDITED` | Human made corrections | `IN_PROGRESS` (resume) |
| `TIMEOUT` | Human review timed out | Terminal |
| `DISPATCHED` | Output sent to CRM/webhook | Terminal |
| `COMPLETED` | All agents executed successfully | Terminal |
| `FAILED` | Max error threshold exceeded | Terminal |

### HITL Request Decision State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: Request created

    PENDING --> APPROVED: Reviewer approves
    PENDING --> REJECTED: Reviewer rejects
    PENDING --> EDITED: Reviewer approves with edits

    APPROVED --> [*]
    REJECTED --> [*]
    EDITED --> [*]
```

### Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> CLOSED: Initial

    CLOSED --> CLOSED: Success
    CLOSED --> OPEN: Failures >= 3

    OPEN --> HALF_OPEN: 30s timeout

    HALF_OPEN --> CLOSED: Probe success
    HALF_OPEN --> OPEN: Probe failure
```

### Event Processing Status State Machine

```mermaid
stateDiagram-v2
    [*] --> processing: Phase 1 - Intent recorded

    processing --> completed: Phase 2 - Workflow submitted
    processing --> orphaned: Process crash (cleanup after 5min)

    orphaned --> [*]: Deleted, retried next cycle
    completed --> [*]: Event fully processed
```

---

## Data Transfer Object Specification

DTOs define the shape of data exchanged between agents and external services. Each DTO is a Pydantic `BaseModel` with strict type enforcement.

### WebPage DTO

| Field | Type | Description |
|:---|:---|:---|
| `url` | `str` | The URL that was fetched |
| `htmlContent` | `str` | Raw HTML content of the page |
| `statusCode` | `int` | HTTP status code |
| `fetchTimeMs` | `int` | Time taken to fetch in milliseconds |

### CompanyProfile DTO

| Field | Type | Default | Description |
|:---|:---|:---:|:---|
| `name` | `str` | Required | Company name |
| `description` | `Optional[str]` | `None` | Business description |
| `employeeCount` | `Optional[int]` | `None` | Number of employees |
| `revenue` | `Optional[str]` | `None` | Revenue range or estimate |
| `location` | `Optional[str]` | `None` | Headquarters location |
| `industries` | `list[str]` | `[]` | Industry classifications |

### TechStackEntry DTO

| Field | Type | Description |
|:---|:---|:---|
| `technology` | `str` | Technology name (e.g., "React", "PostgreSQL") |
| `category` | `str` | Category (e.g., "Frontend", "Database") |
| `confidence` | `float` | Detection confidence score (0.0 - 1.0) |
| `source` | `str` | Detection method (e.g., "script_tag", "meta_tag") |

### JobPosting DTO

| Field | Type | Description |
|:---|:---|:---|
| `title` | `str` | Job title |
| `department` | `str` | Department name |
| `url` | `str` | URL to the job posting |
| `postedDate` | `str` | Date the job was posted |

### EmailValidationResult DTO

| Field | Type | Description |
|:---|:---|:---|
| `email` | `str` | The email address validated |
| `isValid` | `bool` | Whether the email is valid |
| `reason` | `str` | Validation result explanation |

### CompetitorMapping DTO

| Field | Type | Description |
|:---|:---|:---|
| `technology` | `str` | The technology being mapped |
| `competitors` | `list[str]` | List of competitor product names |
| `painPoints` | `dict[str, str]` | Pain points keyed by competitor |

---

## Schema Validation Rules

### ICPCriteria Schema

```mermaid
graph TB
    subgraph Validation["ICPCriteria Validation Rules"]
        I["industries: List[str]<br/>Required, non-empty"]
        MR["min_revenue: int<br/>ge=0"]
        XR["max_revenue: int<br/>ge=0"]
        ME["min_employees: int<br/>ge=0"]
        XE["max_employees: int<br/>ge=0"]
        L["locations: List[str]"]
        T["tech_stack: List[str]"]
        B["behaviors: List[str]"]
        O["operator: str<br/>default='OR'"]
    end

    subgraph ModelValidator["@model_validator(mode='after')"]
        V1["min_revenue <= max_revenue"]
        V2["min_employees <= max_employees"]
    end

    MR & XR --> V1
    ME & XE --> V2
```

The `check_ranges` model validator ensures that minimum values never exceed maximum values, preventing nonsensical ICP criteria.

### ThresholdConfig Schema

| Field | Type | Description | Constraint |
|:---|:---|:---|:---|
| `min_confidence_score` | `float` | Minimum acceptable confidence | 0.0 - 1.0 |
| `max_errors_allowed` | `int` | Maximum errors before pipeline failure | >= 0 |
| `hitl_confidence_threshold` | `float` | Below this, HITL review triggered | 0.0 - 1.0 |
| `auto_approve_threshold` | `float` | Above this, auto-approved | 0.0 - 1.0 |

### PersonaDefinition Schema

| Field | Type | Default | Description |
|:---|:---|:---:|:---|
| `job_titles` | `List[str]` | Required | Target job titles (e.g., "CTO", "VP Engineering") |
| `seniority_levels` | `List[str]` | Required | Target seniority (e.g., "C-Level", "VP") |
| `functions` | `List[str]` | Required | Target functions (e.g., "Engineering", "Product") |
| `exclude_titles` | `List[str]` | `[]` | Titles to exclude from matching |

---

## GraphState Contract Specification

### Complete Field Reference

| Field | Type | Reducer | Default | Description |
|:---|:---|:---|:---:|:---|
| `prospect_id` | `str` | None | `""` | Unique prospect identifier |
| `current_trigger_event` | `str` | None | `""` | Event that triggered the workflow |
| `config` | `Annotated[dict, add_dict]` | `add_dict` | `{}` | Runtime configuration (ICP, persona, thresholds) |
| `data` | `Annotated[dict, add_dict]` | `add_dict` | `{}` | Accumulated agent data (firmographics, tech stack, contacts, etc.) |
| `executed_agents` | `Annotated[list, add_list]` | `add_list` | `[]` | List of agents that have executed |
| `dispatched_agents` | `Annotated[list, add_list]` | `add_list` | `[]` | Agents dispatched for parallel execution |
| `errors` | `Annotated[list, add_list]` | `add_list` | `[]` | Error messages from failed agents |
| `retry_counts` | `Annotated[dict, add_dict]` | `add_dict` | `{}` | Per-agent retry counters |
| `confidence_score` | `float` | None | `0.0` | Overall confidence score (0.0 - 1.0) |
| `has_conflict` | `bool` | None | `False` | Whether data conflicts were detected |
| `validation_notes` | `Annotated[list, add_list]` | `add_list` | `[]` | Validation notes from cross-validator |
| `recent_thoughts` | `Annotated[list, add_list]` | `add_list` | `[]` | Agent reasoning thoughts for SSE broadcast |
| `execution_trace` | `Annotated[list, add_list]` | `add_list` | `[]` | Complete execution audit trail |
| `overall_status` | `str` | None | `"PENDING"` | Current workflow status |
| `human_override_payload` | `str` | None | `""` | HITL reviewer's response payload |
| `next_node` | `str \| list[str]` | None | `""` | Planner's routing decision |
| `last_agent` | `str` | None | `""` | Most recently executed agent name |
| `custom_workflow_steps` | `dict \| list \| None` | None | `None` | Custom DAG definition |
| `custom_workflow_id` | `str` | None | `""` | UUID of attached custom workflow |
| `next_custom_agent` | `str` | None | `""` | Custom agent to execute next |
| `simulate_failure` | `bool` | None | `False` | Testing flag for failure simulation |

### ValidationNote TypedDict

| Field | Type | Description |
|:---|:---|:---|
| `level` | `str` | Severity: `"INFO"`, `"WARN"`, `"ERROR"` |
| `message` | `str` | Human-readable validation message |
| `source_agent` | `str` | Agent that generated the note |
| `timestamp` | `float` | Unix timestamp of the note |

### Reducer Function Specifications

**`add_dict(left: dict, right: dict) -> dict`**

Merges two dictionaries. Right-side values take precedence for conflicting keys:

```python
def add_dict(left: dict, right: dict) -> dict:
    return {**left, **right}
```

**`add_list(left: list, right: list) -> list`**

Concatenates two lists:

```python
def add_list(left: list, right: list) -> list:
    return left + right
```

---

## API Request/Response Contracts

### Prospect Submission

**Request:** `POST /api/prospects`
```json
{
    "company_name": "Acme Corp",
    "website": "https://acme.com"
}
```

**Response:** `200 OK`
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "display_id": "P-001",
    "company_name": "Acme Corp",
    "status": "PENDING",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### HITL Approval

**Request:** `POST /api/hitl/{id}/approve`
```json
{
    "corrections": {
        "firmographics": {
            "employeeCount": 150
        }
    }
}
```

**Response:** `200 OK`
```json
{
    "status": "ok"
}
```

### Custom Agent Creation

**Request:** `POST /api/agents`
```json
{
    "name": "competitive_analyst",
    "description": "Analyzes competitive landscape",
    "system_prompt": "You are a competitive intelligence analyst...",
    "allowed_tools": ["WebSearch", "Crunchbase"]
}
```

### Workflow Creation

**Request:** `POST /api/workflows`
```json
{
    "name": "Fast Qualification",
    "description": "Quick qualification pipeline",
    "steps": {
        "nodes": [
            {"id": "1", "data": {"agentId": "enricher_node"}},
            {"id": "2", "data": {"agentId": "score_node"}}
        ],
        "edges": [
            {"source": "1", "target": "2"}
        ]
    }
}
```

---

## Configuration Schema Design

### Default Configuration Structure

```mermaid
graph TB
    subgraph Defaults["Default Configuration (YAML)"]
        ICP["ICP Criteria"]
        PERSONA["Persona Definition"]
        THRESHOLDS["Scoring Thresholds"]
    end

    subgraph ICP_Detail["ICP Defaults"]
        I1["industries: [SaaS, Enterprise Software, Cloud]"]
        I2["min_revenue: 1,000,000"]
        I3["max_revenue: 500,000,000"]
        I4["min_employees: 50"]
        I5["max_employees: 5000"]
        I6["tech_stack: [React, Node.js, Python, AWS]"]
        I7["behaviors: [Recent funding round, New product launch]"]
        I8["operator: OR"]
    end

    subgraph THRESHOLDS_Detail["Threshold Defaults"]
        T1["min_confidence_score: 30"]
        T2["max_errors_allowed: 5"]
        T3["hitl_confidence_threshold: 40"]
        T4["auto_approve_threshold: 85"]
    end

    ICP --> ICP_Detail
    THRESHOLDS --> THRESHOLDS_Detail
```

### Configuration Layering

```mermaid
graph TB
    subgraph Layers["Configuration Priority (highest first)"]
        L1["1. Per-Workflow State Override<br/>state.config.icp"]
        L2["2. Database Config Table<br/>SELECT FROM config WHERE key='icp'"]
        L3["3. YAML Default File<br/>Bundled with application"]
    end

    L1 -->|"falls through"| L2
    L2 -->|"falls through"| L3
```

---

## Index Strategy

| Table | Column(s) | Index Type | Purpose |
|:---|:---|:---|:---|
| `prospects` | `company_name` | B-tree | Fast company name lookup |
| `prospects` | `status` | B-tree | Status-based filtering |
| `prospects` | `display_id` | B-tree | Human-readable ID lookup |
| `hitl_requests` | `decision` | B-tree | Pending request queries (WHERE decision IS NULL) |
| `hitl_requests` | `display_id` | B-tree | Human-readable ID lookup |
| `custom_agents` | `name` | B-tree | Agent name resolution |
| `workflows` | `name` | B-tree | Workflow name lookup |

---

## Connection Pool Design

### Async Engine Configuration

```mermaid
graph TB
    subgraph Engine["SQLAlchemy Async Engine"]
        URL["Database URL"]
        POOL{"DB Type?"}
        
        subgraph SQLite["SQLite Mode"]
            DEFAULT["Default pool<br/>(for development)"]
        end
        
        subgraph PostgreSQL["PostgreSQL Mode"]
            NULL["NullPool<br/>(fresh connections)"]
        end
    end

    URL --> POOL
    POOL -->|"sqlite"| DEFAULT
    POOL -->|"postgresql"| NULL
```

**NullPool Rationale:** In production with a single worker and multiple background tasks, `NullPool` ensures:
- No stale connections in pool
- No connection leak from orphaned checkouts
- Each operation gets a fresh connection
- Connection closure is deterministic

### Session Factory Pattern

```mermaid
graph LR
    SF["async_session (Factory)"] -->|"creates"| S1["Session 1<br/>(short-lived)"]
    SF -->|"creates"| S2["Session 2<br/>(short-lived)"]
    SF -->|"creates"| S3["Session 3<br/>(short-lived)"]
    
    S1 -->|"auto-close"| DONE["Closed"]
    S2 -->|"auto-close"| DONE
    S3 -->|"auto-close"| DONE
```

The `MemoryService` and `dependencies.py` both use the session factory pattern:

```python
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

This ensures every database operation uses a fresh, properly scoped session that is automatically closed when the operation completes.

---

<p align="center">
  <a href="README.md">Backend README</a> &#8226;
  <a href="CLASS_DIAGRAM.md">Class Diagrams</a> &#8226;
  <a href="SEQUENCE_FLOW.md">Sequence Flows</a> &#8226;
  <a href="SOLID_PRINCIPLES.md">SOLID</a> &#8226;
  <a href="RELIABILITY.md">Reliability</a> &#8226;
  <a href="AGENTIC_FLOW.md">Agentic Flow</a> &#8226;
  <a href="APPLICATION_FLOW.md">App Flow</a>
</p>
