<h1 align="center">Application Flow Reference</h1>

<p align="center">
  <strong>End-to-end application flow documentation covering infrastructure bootstrap, request handling lifecycle, agent execution pipeline, real-time event delivery, and graceful shutdown -- from first byte to final response.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Bootstrap-Lifespan_Managed-009688?style=for-the-badge" alt="Bootstrap">
  <img src="https://img.shields.io/badge/Execution-Async_Pipeline-FF6F00?style=for-the-badge" alt="Execution">
  <img src="https://img.shields.io/badge/Events-SSE_Real_Time-9C27B0?style=for-the-badge" alt="Events">
  <img src="https://img.shields.io/badge/Shutdown-Graceful-4CAF50?style=for-the-badge" alt="Shutdown">
</p>

---

## Table of Contents

- [Application Bootstrap Flow](#application-bootstrap-flow)
- [Request Handling Pipeline](#request-handling-pipeline)
- [Agent Execution Pipeline](#agent-execution-pipeline)
- [Real-Time Event Delivery](#real-time-event-delivery)
- [Background Task Management](#background-task-management)
- [Trigger Monitor Lifecycle](#trigger-monitor-lifecycle)
- [Graceful Shutdown Flow](#graceful-shutdown-flow)
- [Full System Interaction Map](#full-system-interaction-map)
- [Thread and Concurrency Model](#thread-and-concurrency-model)
- [Error Propagation Flow](#error-propagation-flow)

---

## Application Bootstrap Flow

The application uses FastAPI's `lifespan` context manager to bootstrap all services, establish database connections, and initialize the agent graph before accepting any requests.

```mermaid
sequenceDiagram
    participant UV as Uvicorn
    participant FA as FastAPI
    participant LS as Lifespan (startup.py)
    participant DB as PostgreSQL
    participant LLM as LLMService
    participant SC as ScrapingService
    participant EN as EnrichmentService
    participant TB as Toolbox
    participant MS as MemoryService
    participant CS as ConfigService
    participant GR as LangGraph
    participant HS as HITLService
    participant WS as WorkflowService
    participant TM as TriggerMonitor

    UV->>FA: Start application
    FA->>LS: Enter lifespan context

    Note over LS: Phase 1: Database Initialization
    LS->>DB: init_db() -- CREATE TABLE IF NOT EXISTS
    DB-->>LS: Tables ready

    Note over LS: Phase 2: Service Instantiation
    LS->>LLM: LLMService()
    LS->>SC: ScrapingService()
    LS->>EN: EnrichmentService()

    Note over LS: Phase 3: Facade Assembly
    LS->>TB: Toolbox(llm, scraping, enrichment)

    Note over LS: Phase 4: Memory Layer
    LS->>MS: MemoryService(async_session factory)

    Note over LS: Phase 5: Configuration Preload
    LS->>CS: ConfigService(session)
    LS->>CS: get_icp()
    CS->>DB: SELECT FROM config WHERE key='icp'
    CS-->>LS: ICP criteria
    LS->>CS: get_persona()
    CS-->>LS: Persona definition

    Note over LS: Phase 6: Graph Compilation
    LS->>GR: get_app(toolbox, memory, config)
    GR->>GR: setup_graph() -- build StateGraph
    GR->>GR: Register all agents from AgentRegistry
    GR->>GR: Wrap in SafeAgentWrapper
    GR->>GR: Wire conditional edges
    GR->>DB: Create AsyncPostgresSaver pool
    GR->>GR: Compile graph with checkpointer
    GR-->>LS: (compiled_app, pool)

    Note over LS: Phase 7: Workflow and HITL Wiring
    LS->>HS: HITLService(memory)
    LS->>WS: WorkflowService(graph_app, hitl)
    LS->>HS: Set workflow_service (bidirectional link)

    Note over LS: Phase 8: Trigger Monitor
    LS->>TM: TriggerMonitor(toolbox, workflow_service)

    Note over LS: Phase 9: Store on app.state
    LS->>FA: Store all services on app.state
    FA-->>UV: Application ready to accept requests
```

### Bootstrap Design Principles

| Principle | Implementation |
|:---|:---|
| **Explicit Dependency Graph** | Services are instantiated in dependency order -- no circular initialization |
| **No Hidden Singletons** | All services are created during lifespan and stored on `app.state` |
| **Configuration Preloading** | ICP and persona configs are loaded once at startup, not on every request |
| **Safe Re-entry** | `init_db()` uses `CREATE TABLE IF NOT EXISTS`, safe to run on every startup |
| **Conditional Initialization** | `init_db()` is skipped in test environments (`APP_ENV != "test"`) |

---

## Request Handling Pipeline

### Prospect Submission (POST /api/prospects)

```mermaid
graph TB
    subgraph HTTP["HTTP Layer"]
        REQ["POST /api/prospects<br/>{company_name, website}"]
        CORS["CORS Middleware"]
        ROUTE["prospects.router"]
    end

    subgraph Validation["Validation Layer"]
        PARSE["Parse request body"]
        UUID["Generate prospect UUID"]
        DID["Generate display_id (P-NNN)"]
    end

    subgraph Persistence["Persistence Layer"]
        STATE["Build initial GraphState"]
        SAVE["MemoryService.save_prospect_state()"]
        DB["INSERT INTO prospects"]
    end

    subgraph Execution["Async Execution"]
        WS["WorkflowService.submit_prospect()"]
        TASK["asyncio.create_task()"]
        DETACH["Task runs in background"]
    end

    subgraph Response["Response"]
        RES["Return prospect summary"]
        SSE["SSE stream available at /stream"]
    end

    REQ --> CORS --> ROUTE
    ROUTE --> PARSE --> UUID --> DID
    DID --> STATE --> SAVE --> DB
    DB --> WS --> TASK --> DETACH
    DETACH --> RES
    RES -.-> SSE
```

### Request-Scoped Dependencies

```mermaid
graph LR
    subgraph Dependencies["Dependency Injection per Request"]
        REQ["Incoming Request"]
        GS["get_session() -> AsyncSession"]
        GMS["get_memory_service() -> MemoryService"]
        APP["request.app.state -> WorkflowService, HITLService, etc."]
    end

    REQ --> GS
    REQ --> GMS
    REQ --> APP
```

The dependency injection follows two patterns:
1. **Lifespan-scoped** -- Long-lived services (`WorkflowService`, `Toolbox`) stored on `app.state`
2. **Request-scoped** -- Short-lived resources (`AsyncSession`, `MemoryService`) created per-request via FastAPI `Depends()`

---

## Agent Execution Pipeline

### Single Agent Execution Cycle

```mermaid
graph TB
    subgraph Planner["DynamicPlanner Decision"]
        P1["Inspect GraphState"]
        P2["Query AgentRegistry"]
        P3["Construct LLM prompt"]
        P4["Parse routing response"]
        P5["Set next_node"]
    end

    subgraph Wrapper["SafeAgentWrapper"]
        W1["Record start time"]
        W2["Call agent.__call__(state)"]
        W3["Record end time"]
        W4["Build execution trace"]
        W5["Set last_agent"]
    end

    subgraph Agent["Worker Agent"]
        A1["Read required state fields"]
        A2["Call Toolbox methods"]
        A3["Process results"]
        A4["Return state delta"]
    end

    subgraph Merge["State Merge"]
        M1["Annotated reducers merge delta"]
        M2["Updated state available"]
    end

    P1 --> P2 --> P3 --> P4 --> P5
    P5 --> W1 --> W2
    W2 --> A1 --> A2 --> A3 --> A4
    A4 --> W3 --> W4 --> W5
    W5 --> M1 --> M2
    M2 -->|"loop"| P1
```

### Data Flow Through Agent Pipeline

```mermaid
graph LR
    subgraph Pipeline["Data Accumulation Through Pipeline"]
        S1["State after Researcher:<br/>data.market_context = '...'<br/>data.competitors_context = '...'"]
        S2["State after Enricher:<br/>+ data.firmographics = {...}<br/>+ data.website_url = '...'"]
        S3["State after TechStack:<br/>+ data.tech_stack = [...]"]
        S4["State after Score:<br/>+ data.scored_signals = [...]<br/>+ confidence_score = 0.72"]
        S5["State after Summarizer:<br/>+ data.summary_object = {...}"]
    end

    S1 --> S2 --> S3 --> S4 --> S5
```

Each agent adds its output to the `data` dict, which is merged via the `add_dict` reducer. Downstream agents can read data from all upstream agents.

---

## Real-Time Event Delivery

### SSE Architecture

```mermaid
graph TB
    subgraph Sources["Event Sources"]
        AGENT["Agent Execution<br/>(recent_thoughts)"]
        WF["Workflow Service<br/>(state_update)"]
        HITL["HITL Events<br/>(interrupt)"]
    end

    subgraph Broker["PubSub Broker"]
        TOPIC["Topic: prospect_id"]
        QUEUE["asyncio.Queue per subscriber"]
    end

    subgraph Delivery["SSE Delivery"]
        ENDPOINT["/api/prospects/{id}/stream"]
        FORMAT["text/event-stream"]
        CLIENT["Browser EventSource"]
    end

    AGENT -->|publish| TOPIC
    WF -->|publish| TOPIC
    HITL -->|publish| TOPIC
    TOPIC --> QUEUE
    QUEUE --> ENDPOINT
    ENDPOINT -->|SSE events| FORMAT
    FORMAT --> CLIENT
```

### SSE Event Types

| Event Type | Content | Trigger |
|:---|:---|:---|
| `thought` | Agent reasoning and decisions | `on_chain_end` during workflow execution |
| `action` | Agent completion notification | Detected in `recent_thoughts` list |
| `state_update` | Full state snapshot | After each agent completion |
| `interrupt` | HITL request details | When `HitlGatewayNode` triggers interrupt |

### SSE Connection Lifecycle

```mermaid
sequenceDiagram
    participant Browser
    participant SSE as SSE Endpoint
    participant PS as PubSub
    participant WF as Workflow

    Browser->>SSE: GET /api/prospects/{id}/stream
    SSE->>PS: subscribe(prospect_id)
    PS-->>SSE: asyncio.Queue

    loop While connected
        WF->>PS: publish(prospect_id, event)
        PS->>SSE: Queue.get()
        SSE-->>Browser: data: {"type": "thought", ...}
    end

    Browser->>SSE: Connection closed
    SSE->>PS: unsubscribe(prospect_id, queue)
    PS->>PS: Clean up empty topic
```

---

## Background Task Management

### Task Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: asyncio.create_task()
    Created --> Running: Event loop schedules
    Running --> Completed: Workflow finishes
    Running --> Failed: Unhandled exception
    Running --> Interrupted: HITL pause
    
    Completed --> Cleaned: done_callback removes from set
    Failed --> Cleaned: done_callback removes from set
    Interrupted --> Waiting: State checkpointed
    
    Waiting --> Resumed: HITL decision received
    Resumed --> Running: New task created
    
    Cleaned --> [*]
```

### Task Set Management

The `WorkflowService` maintains a `set[asyncio.Task]` for background workflow tasks:

```python
self._tasks: set[asyncio.Task] = set()

task = asyncio.create_task(self._run_workflow(state, config))
self._tasks.add(task)
task.add_done_callback(self._tasks.discard)
```

The `done_callback` pattern ensures tasks are automatically removed from the set when they complete, preventing memory leaks from accumulating references to finished tasks.

---

## Trigger Monitor Lifecycle

### Monitor State Machine

```mermaid
stateDiagram-v2
    [*] --> Stopped: Initial state

    Stopped --> Starting: POST /api/triggers/start
    Starting --> Running: Background task created

    Running --> Running: Poll cycle completes
    Running --> Stopping: POST /api/triggers/stop
    Running --> Stopping: Process shutdown

    Stopping --> Stopped: _running flag cleared
```

### Poll Cycle Flow

```mermaid
graph TB
    START["Poll cycle begins"]
    CLEAN["_cleanup_orphaned_events()"]
    LOAD["Load enabled trigger sources"]
    
    subgraph Loop["For each source"]
        CHECK["Check polling interval"]
        SKIP["Skip (not ready)"]
        FETCH["APIProviderFactory.get_provider().fetch_entries()"]
        
        subgraph Events["For each event"]
            HASH["Compute event hash"]
            DEDUP["Check processed_events table"]
            NEW["Mark as 'processing' (Outbox Phase 1)"]
            SAVE["Save prospect state"]
            SUBMIT["WorkflowService.submit_prospect()"]
            COMPLETE["Mark as 'completed' (Outbox Phase 2)"]
            SLEEP["Sleep 15s (rate limit)"]
        end
    end

    POLL_SLEEP["Sleep 60s"]
    REPEAT["Next cycle"]

    START --> CLEAN --> LOAD --> Loop
    Loop --> CHECK
    CHECK -->|not ready| SKIP
    CHECK -->|ready| FETCH
    FETCH --> Events
    Events --> HASH --> DEDUP
    DEDUP -->|exists| SKIP
    DEDUP -->|new| NEW --> SAVE --> SUBMIT --> COMPLETE --> SLEEP
    SKIP --> POLL_SLEEP
    SLEEP --> POLL_SLEEP
    POLL_SLEEP --> REPEAT
    REPEAT --> START
```

---

## Graceful Shutdown Flow

```mermaid
sequenceDiagram
    participant UV as Uvicorn
    participant FA as FastAPI
    participant LS as Lifespan
    participant TM as TriggerMonitor
    participant POOL as Checkpointer Pool
    participant TASKS as Background Tasks

    UV->>FA: SIGTERM received
    FA->>LS: Exit lifespan context (finally block)

    Note over LS: Phase 1: Stop Trigger Monitor
    LS->>TM: stop()
    TM->>TM: Set _running = False
    TM->>TM: Cancel background task
    Note over TM: Current poll cycle completes gracefully

    Note over LS: Phase 2: Close Checkpointer Pool
    LS->>POOL: pool.close()
    POOL->>POOL: Close all PostgreSQL connections
    Note over POOL: LangGraph checkpointer connections released

    Note over LS: Phase 3: Background Tasks
    Note over TASKS: Running tasks complete naturally
    Note over TASKS: asyncio event loop cleanup handles remaining

    LS->>FA: Lifespan context exited
    FA->>UV: Application stopped
```

### Shutdown Guarantees

| Guarantee | Mechanism |
|:---|:---|
| No orphaned connections | `NullPool` ensures connections are not pooled |
| Trigger monitor stops cleanly | `_running` flag checked at each loop iteration |
| Checkpointer connections released | `pool.close()` called in `finally` block |
| No data loss for in-progress workflows | LangGraph checkpointer has already persisted state |

---

## Full System Interaction Map

```mermaid
graph TB
    subgraph External["External World"]
        USER["User/Browser"]
        RSS["RSS Feeds"]
        NEWS["News APIs"]
        GH["GitHub"]
        LI["LinkedIn"]
        TAVILY["Tavily"]
        CRM["CRM Webhook"]
    end

    subgraph API["API Gateway"]
        FA["FastAPI<br/>(CORS + Routes)"]
    end

    subgraph Core["Application Core"]
        WS["WorkflowService"]
        HS["HITLService"]
        CS["ConfigService"]
        TM["TriggerMonitor"]
    end

    subgraph Agent["Agent Engine"]
        LG["LangGraph Runtime"]
        DP["DynamicPlanner"]
        FLEET["Agent Fleet (16)"]
        SAW["SafeAgentWrapper"]
    end

    subgraph Services["Service Layer"]
        TB["Toolbox (Facade)"]
        LLM["LLMService"]
        SS["ScrapingService"]
        ES["EnrichmentService"]
        MS["MemoryService"]
    end

    subgraph Infra["Infrastructure"]
        PG["PostgreSQL"]
        PS["PubSub"]
        CB["CircuitBreaker"]
    end

    USER -->|REST| FA
    USER -->|SSE| FA
    FA --> WS & HS & CS
    FA --> MS
    
    WS --> LG
    LG --> DP
    DP --> FLEET
    FLEET --> SAW
    SAW --> TB
    
    TB --> LLM & SS & ES
    TB --> CB
    
    LLM --> TAVILY
    TM --> RSS & NEWS & GH & LI
    TM --> WS
    
    MS --> PG
    LG --> PG
    WS --> PS
    PS --> FA
    
    WS --> CRM
```

---

## Thread and Concurrency Model

### Single-Worker Architecture

The application runs with a single Uvicorn worker (`WORKERS=1`). This is an intentional design decision documented in `docker-compose.yml`:

```yaml
# Single worker required: PubSub, CircuitBreaker, and TriggerMonitor
# are all in-process. Multi-worker would cause duplicate polling and
# missing SSE events. Switch to Redis-backed variants for multi-worker.
- WORKERS=1
```

### Concurrency Within the Worker

```mermaid
graph TB
    subgraph Worker["Single Uvicorn Worker (asyncio event loop)"]
        subgraph Tasks["Concurrent asyncio Tasks"]
            REQ["HTTP Request Handlers"]
            WF1["Workflow Task 1"]
            WF2["Workflow Task 2"]
            WFN["Workflow Task N"]
            POLL["TriggerMonitor Poll Loop"]
            SSE1["SSE Stream 1"]
            SSE2["SSE Stream 2"]
        end
    end

    Note["All tasks share one event loop<br/>Cooperative multitasking via await"]
```

The single-worker model with asyncio provides sufficient concurrency for the target workload while avoiding the complexity of distributed state synchronization.

---

## Error Propagation Flow

```mermaid
graph TB
    subgraph Agent["Agent Level"]
        AE["Agent throws exception"]
    end

    subgraph Wrapper["SafeAgentWrapper Level"]
        CATCH["Exception caught"]
        CHECK{"GraphInterrupt?"}
        RERAISE["Re-raise for LangGraph"]
        RECORD["Record error in state"]
    end

    subgraph Planner["Planner Level"]
        READ["Read errors from state"]
        DECIDE{"Max errors exceeded?"}
        SKIP["Route to different agent"]
        HALT["Set status = FAILED"]
    end

    subgraph Service["Service Level"]
        LOG["structlog records error"]
        METRIC["MonitoringService.log_error()"]
    end

    subgraph Persistence["Persistence Level"]
        SAVE["Error persisted in state_json"]
        DB["PostgreSQL"]
    end

    AE --> CATCH
    CATCH --> CHECK
    CHECK -->|Yes| RERAISE
    CHECK -->|No| RECORD
    RECORD --> READ
    READ --> DECIDE
    DECIDE -->|No| SKIP
    DECIDE -->|Yes| HALT
    
    RECORD --> LOG
    LOG --> METRIC
    RECORD --> SAVE
    SAVE --> DB
```

---

<p align="center">
  <a href="README.md">Backend README</a> &#8226;
  <a href="CLASS_DIAGRAM.md">Class Diagrams</a> &#8226;
  <a href="SEQUENCE_FLOW.md">Sequence Flows</a> &#8226;
  <a href="SOLID_PRINCIPLES.md">SOLID</a> &#8226;
  <a href="RELIABILITY.md">Reliability</a> &#8226;
  <a href="AGENTIC_FLOW.md">Agentic Flow</a> &#8226;
  <a href="LLD_ARCHITECTURE.md">LLD</a>
</p>
