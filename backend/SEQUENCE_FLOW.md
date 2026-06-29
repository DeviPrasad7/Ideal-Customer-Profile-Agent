<h1 align="center">Sequence Flow Reference</h1>

<p align="center">
  <strong>End-to-end sequence diagrams for every major workflow in the ICP Agent platform -- from prospect submission through agent orchestration, human review, trigger processing, and custom agent execution.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Diagrams-Mermaid-8A2BE2?style=for-the-badge" alt="Mermaid">
  <img src="https://img.shields.io/badge/Workflows-7_Flows-FF6F00?style=for-the-badge" alt="Flows">
  <img src="https://img.shields.io/badge/Coverage-End_to_End-4CAF50?style=for-the-badge" alt="Coverage">
</p>

---

## Table of Contents

- [Prospect Submission Flow](#prospect-submission-flow)
- [Agent Orchestration Flow](#agent-orchestration-flow)
- [Human-in-the-Loop Review Flow](#human-in-the-loop-review-flow)
- [Trigger Monitor Event Processing](#trigger-monitor-event-processing)
- [Custom Agent Execution Flow](#custom-agent-execution-flow)
- [LLM Multi-Provider Failover](#llm-multi-provider-failover)
- [Real-Time SSE Event Delivery](#real-time-sse-event-delivery)
- [Configuration Update Flow](#configuration-update-flow)
- [Custom Workflow DAG Execution](#custom-workflow-dag-execution)

---

## Prospect Submission Flow

This sequence captures the complete lifecycle of a prospect from API submission through workflow execution, agent processing, and state persistence.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI Route
    participant WS as WorkflowService
    participant CS as ConfigService
    participant DB as PostgreSQL
    participant MS as MemoryService
    participant LG as LangGraph
    participant DP as DynamicPlanner
    participant PS as PubSub

    User->>FE: Submit company name
    FE->>API: POST /api/prospects {company_name}
    API->>DB: Generate UUID prospect_id
    API->>MS: save_prospect_state(initial_state)
    MS->>DB: INSERT INTO prospects
    API->>WS: submit_prospect(state, thread_id)
    
    Note over WS: Background asyncio.Task created
    
    WS->>CS: get_icp(), get_persona(), get_thresholds()
    CS->>DB: SELECT FROM config
    CS-->>WS: Config data
    WS->>WS: Inject config into state
    
    WS->>LG: astream_events(state, config)
    LG->>DP: Execute dynamic_planner
    DP-->>LG: {next_node: "enricher_node"}
    
    Note over LG: See Agent Orchestration Flow
    
    loop For each agent execution
        LG->>LG: Execute agent node
        LG-->>WS: on_chain_end event
        WS->>PS: publish(thread_id, thought)
        WS->>PS: publish(thread_id, state_update)
        WS->>MS: save_prospect_state(current_state)
        MS->>DB: UPDATE prospects SET state_json
    end
    
    WS->>LG: aget_state(config)
    LG-->>WS: state_snapshot
    
    alt Workflow paused (interrupt)
        WS->>WS: Extract interrupt data
        WS->>WS: hitl_service.create_request()
    else Workflow completed
        WS->>WS: Log completion
    end
    
    API-->>FE: {prospect_id, status: "submitted"}
    FE-->>User: Show prospect in pipeline
```

**Key Engineering Details:**
- The workflow runs as a detached `asyncio.Task`, allowing the API to return immediately with a 202 Accepted-style response
- Each agent execution triggers an intermediate state persistence to PostgreSQL, enabling crash recovery
- The `PubSub` broker broadcasts real-time thoughts and state updates to any connected SSE subscribers
- The `WorkflowService` stores all background tasks in a `set()` with done callbacks for proper garbage collection

---

## Agent Orchestration Flow

This sequence details how the `DynamicPlannerNode` orchestrates the agent fleet using its three-tier routing strategy.

```mermaid
sequenceDiagram
    participant LG as LangGraph Runtime
    participant DP as DynamicPlanner
    participant REG as AgentRegistry
    participant LLM as LLMService
    participant SAW as SafeAgentWrapper
    participant Agent as Worker Agent
    participant State as GraphState

    LG->>DP: __call__(state)
    
    alt Custom Workflow Attached
        DP->>State: Read custom_workflow_steps
        DP->>DP: Parse DAG nodes and edges
        DP->>DP: Check dependency satisfaction
        DP->>DP: Collect ready-to-run agents
        DP-->>LG: {next_node: [parallel_agents]}
    else Standard LLM Routing
        DP->>REG: list_agents_with_descriptions()
        REG-->>DP: Available agents with descriptions
        DP->>DP: Filter out already-executed agents
        DP->>DP: Truncate context data for token savings
        DP->>DP: Construct routing prompt
        DP->>LLM: generate_text(prompt, strategy="fast")
        LLM-->>DP: {"next_node": "enricher_node", "reasoning": "..."}
        DP->>DP: Validate response against registry
        DP-->>LG: {next_node: "enricher_node"}
    else LLM Failure (Fallback)
        DP->>DP: Deterministic linear sequence
        DP-->>LG: {next_node: next_unexecuted_agent}
    end

    LG->>SAW: __call__(state)
    Note over SAW: SafeAgentWrapper intercepts

    SAW->>SAW: Record start_time
    SAW->>Agent: __call__(state)
    
    alt Success
        Agent-->>SAW: result dict
        SAW->>SAW: Record execution trace
        SAW->>SAW: Set last_agent
        SAW-->>LG: result with trace
    else Unhandled Exception
        SAW->>SAW: Check if GraphInterrupt
        alt Graph Control Flow
            SAW-->>LG: Re-raise interrupt
        else Application Error
            SAW->>SAW: Increment retry_counts
            SAW->>SAW: Log error via structlog
            SAW-->>LG: {errors: [...], retry_counts: {...}}
        end
    end

    LG->>DP: Return to planner
    Note over DP: Cycle repeats until __end__
```

**Key Engineering Details:**
- The planner constructs a token-optimized prompt by truncating context data to 150 characters per field and limiting list items to 3
- Agent descriptions are capped at 80 characters in the routing prompt to reduce token consumption
- The `SafeAgentWrapper` explicitly checks for `GraphInterrupt` and `NodeInterrupt` exceptions, allowing LangGraph control flow to propagate while catching all application-level errors
- Retry counts are tracked per-agent in the graph state, enabling the planner to make informed retry/skip decisions

---

## Human-in-the-Loop Review Flow

This sequence captures the complete HITL lifecycle from interrupt creation through human review and workflow resumption.

```mermaid
sequenceDiagram
    actor Reviewer
    participant FE as Frontend
    participant API as FastAPI Route
    participant HS as HITLService
    participant MS as MemoryService
    participant DB as PostgreSQL
    participant WS as WorkflowService
    participant LG as LangGraph
    participant HITL as HitlGatewayNode

    Note over HITL: During workflow execution...
    
    HITL->>HITL: Evaluate confidence vs thresholds
    
    alt Auto-Approve (confidence >= auto_threshold)
        HITL-->>LG: {overall_status: "APPROVED"}
    else Needs Human Review
        HITL->>LG: interrupt({prospect_id, reason, state})
        Note over LG: Workflow execution pauses
        LG->>WS: State snapshot with interrupts
        WS->>HS: create_request(prospect_id, interrupt_data)
        HS->>MS: create_hitl_request(prospect_id, summary)
        MS->>DB: INSERT INTO hitl_requests
        MS->>DB: UPDATE prospects SET status='PENDING_HUMAN'
    end

    Note over FE: Reviewer opens HITL Queue

    FE->>API: GET /api/hitl/pending
    API->>MS: get_pending_hitl_requests()
    MS->>DB: SELECT FROM hitl_requests WHERE decision IS NULL
    DB-->>MS: Pending requests with prospect data
    MS-->>API: List of HITL requests
    API-->>FE: Render review queue

    Reviewer->>FE: Review prospect data
    Reviewer->>FE: Click Approve (with optional edits)
    FE->>API: POST /api/hitl/{id}/approve {corrections}

    API->>HS: resolve_request(id, "APPROVED", corrections)
    HS->>MS: resolve_hitl_request_and_update_prospect()
    MS->>DB: UPDATE hitl_requests SET decision='APPROVED'
    MS->>DB: UPDATE prospects SET status='APPROVED'
    MS-->>HS: workflow_thread_id

    HS->>WS: resume_with_hitl(thread_id, "APPROVED", corrections)
    
    Note over WS: Background asyncio.Task created

    WS->>LG: astream_events(Command(resume=payload), config)
    LG->>HITL: Resume with response
    HITL->>HITL: Apply edits to state
    HITL-->>LG: {overall_status: "APPROVED"}
    
    LG->>LG: Continue to output_dispatcher_node
    LG-->>WS: Workflow complete

    API-->>FE: {status: "ok"}
    FE-->>Reviewer: Show success notification
```

**Key Engineering Details:**
- The HITL gateway supports three confidence tiers: auto-approve (above threshold), human review (below threshold), and auto-reject (missing critical data)
- All DB operations in `resolve_request` execute in a single `AsyncSession` block with `selectinload` to prevent detached-ORM errors
- The workflow resumes **after** the database commit is durable, ensuring data consistency
- Corrections from the reviewer are merged into the graph state via the `data` field, allowing downstream agents to work with human-corrected data

---

## Trigger Monitor Event Processing

This sequence shows the event-driven trigger system with its outbox pattern for guaranteed delivery.

```mermaid
sequenceDiagram
    participant TM as TriggerMonitor
    participant DB as PostgreSQL
    participant APF as APIProviderFactory
    participant Provider as API Provider
    participant MS as MemoryService
    participant WS as WorkflowService
    participant LG as LangGraph

    Note over TM: Background polling loop (60s interval)

    TM->>TM: _cleanup_orphaned_events()
    TM->>DB: SELECT FROM processed_events WHERE status='processing' AND age > 5min
    DB-->>TM: Orphaned events
    TM->>DB: DELETE orphaned events
    Note over TM: Orphans will be retried on next cycle

    TM->>DB: SELECT FROM trigger_sources WHERE enabled=true
    DB-->>TM: Active trigger sources

    loop For each trigger source
        TM->>TM: Check polling interval
        alt Interval not elapsed
            TM->>TM: Skip source
        else Ready to poll
            TM->>APF: get_provider(source.type)
            APF-->>TM: Concrete provider instance
            TM->>Provider: fetch_entries(config)
            Provider-->>TM: Raw event entries

            loop For each event entry
                TM->>MS: has_event_been_processed(hash)
                MS->>DB: SELECT FROM processed_events
                
                alt Already processed
                    TM->>TM: Skip event
                else New event
                    TM->>TM: Generate prospect UUID
                    
                    Note over TM: OUTBOX PHASE 1: Mark intent
                    TM->>MS: mark_event_processed(hash, "processing")
                    MS->>DB: INSERT processed_events(status='processing')
                    
                    TM->>MS: save_prospect_state(initial_state)
                    MS->>DB: INSERT INTO prospects
                    
                    TM->>WS: submit_prospect(state, thread_id)
                    
                    Note over TM: OUTBOX PHASE 2: Confirm delivery
                    TM->>MS: update_event_status(hash, "completed")
                    MS->>DB: UPDATE processed_events SET status='completed'
                    
                    TM->>TM: Sleep 15s (rate limit protection)
                end
            end
        end
    end

    TM->>TM: Sleep 60s
    Note over TM: Loop repeats
```

**Key Engineering Details:**
- The outbox pattern ensures exactly-once processing: events are marked `"processing"` before submission and `"completed"` after successful dispatch
- If the process crashes between Phase 1 and Phase 2, the orphan cleanup job deletes stale `"processing"` rows after 5 minutes, allowing retry on the next poll cycle
- A 15-second sleep between prospect submissions protects free-tier LLM rate limits from burst traffic
- A 0.5-second global safety sleep between provider calls prevents burst rate limiting across API providers
- The `mark_event_processed` method uses database-level `IntegrityError` handling to prevent duplicate processing by concurrent workers

---

## Custom Agent Execution Flow

This sequence details how user-created custom agents are executed through the `DynamicAgentExecutorNode`.

```mermaid
sequenceDiagram
    participant DP as DynamicPlanner
    participant LG as LangGraph
    participant DAE as DynamicAgentExecutor
    participant DB as PostgreSQL
    participant Tools as Tool Registry
    participant LLM as LLMService
    participant ReAct as ReAct Agent

    DP->>DP: LLM selects custom agent
    DP->>DB: Verify agent exists in custom_agents table
    DP-->>LG: {next_node: "dynamic_agent_executor", next_custom_agent: "my_agent"}

    LG->>DAE: __call__(state)
    DAE->>DAE: Read next_custom_agent from state
    DAE->>DB: SELECT FROM custom_agents WHERE name='my_agent'
    DB-->>DAE: Agent definition (system_prompt, allowed_tools)

    alt Agent has tools
        DAE->>Tools: get_agent_tools(toolbox, agent_id)
        Tools-->>DAE: {WebSearch, Crunchbase, LinkedIn, EmployeeSearch}
        DAE->>DAE: Filter by agent's allowed_tools list
        DAE->>LLM: get_llm(strategy="heavy")
        LLM-->>DAE: Chat model instance
        DAE->>ReAct: create_react_agent(llm, tools, system_prompt)
        DAE->>ReAct: ainvoke({messages: [task + state_data]})
        
        loop ReAct Loop
            ReAct->>LLM: Generate action
            LLM-->>ReAct: Tool call decision
            ReAct->>Tools: Execute tool
            Tools-->>ReAct: Tool result
            ReAct->>LLM: Observe result, decide next
        end
        
        ReAct-->>DAE: Final response
    else No tools (simple generation)
        DAE->>LLM: generate_text(system_prompt + state_data)
        LLM-->>DAE: Generated response
    end

    DAE-->>LG: {data: {my_agent_output: response}, executed_agents: [...]}
    LG->>DP: Return to planner
```

**Key Engineering Details:**
- Custom agents are defined in the database with a system prompt and an allowed tools list, making them fully user-configurable at runtime
- When tools are enabled, the executor builds a LangChain ReAct agent that autonomously decides which tools to call based on its system prompt
- Tool execution includes real-time log emission via `Toolbox.emit_event()`, enabling the frontend to display custom agent execution logs in real-time
- The output is stored under `data[<agent_name>_output]` in the graph state, making it accessible to all downstream agents

---

## LLM Multi-Provider Failover

This sequence shows the resilient LLM call path with dual-pool failover and global rate limiting.

```mermaid
sequenceDiagram
    participant Caller as Agent / Service
    participant LLM as LLMService
    participant Lock as Global Async Lock
    participant Groq as Groq Pool
    participant Gemini as Gemini Pool

    Caller->>LLM: generate_text(prompt, fallback)
    LLM->>LLM: _ensure_initialized()
    LLM->>LLM: Truncate prompt to 20k chars

    Note over LLM: Try Groq pool first (higher rate limits)

    loop For each model in Groq pool
        LLM->>Lock: Acquire global lock
        Lock->>Lock: Check time since last call
        alt Elapsed < 2.5s
            Lock->>Lock: Sleep(2.5 - elapsed)
        end
        Lock->>LLM: Lock acquired
        
        LLM->>Groq: ainvoke(messages)
        
        alt Success
            Groq-->>LLM: Response content
            LLM->>LLM: Rotate model to end of pool
            LLM-->>Caller: Response text
        else Failure
            Groq-->>LLM: Exception
            LLM->>LLM: Log warning, rotate, try next
        end
    end

    Note over LLM: Groq exhausted, try Gemini pool

    loop For each model in Gemini pool
        LLM->>Lock: Acquire global lock
        LLM->>Gemini: ainvoke(messages)
        
        alt Success
            Gemini-->>LLM: Response content
            LLM-->>Caller: Response text
        else Failure
            Gemini-->>LLM: Exception
            LLM->>LLM: Log warning, try next
        end
    end

    Note over LLM: All pools exhausted

    LLM-->>Caller: Return fallback response
```

---

## Real-Time SSE Event Delivery

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as SSE Endpoint
    participant PS as PubSub Broker
    participant WS as WorkflowService
    participant Agent as Agent Node

    FE->>API: GET /api/prospects/{id}/stream
    API->>PS: subscribe(prospect_id)
    PS-->>API: asyncio.Queue

    Note over API: SSE connection held open

    Agent->>Agent: Execute logic
    Agent-->>WS: Return result with recent_thoughts
    WS->>PS: publish(thread_id, {type: "thought", agent, message})
    PS->>API: Queue receives message
    API-->>FE: SSE event: {type: "thought", ...}

    WS->>WS: aget_state(config)
    WS->>PS: publish(thread_id, {type: "state_update", payload})
    PS->>API: Queue receives message
    API-->>FE: SSE event: {type: "state_update", ...}

    Note over FE: UI updates in real-time

    FE->>API: Connection closed
    API->>PS: unsubscribe(prospect_id, queue)
```

---

## Configuration Update Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI Route
    participant CS as ConfigService
    participant DB as PostgreSQL
    participant Schema as Pydantic Schema

    User->>FE: Edit ICP criteria
    FE->>API: PUT /api/config/icp {industries, min_revenue, ...}
    API->>Schema: ICPCriteria.model_validate(data)
    
    alt Validation passes
        Schema-->>API: Valid ICPCriteria instance
        API->>CS: update_icp(criteria)
        CS->>DB: SELECT FROM config WHERE key='icp'
        
        alt Config exists
            CS->>DB: UPDATE config SET value={...}
        else Config missing
            CS->>DB: INSERT INTO config
        end
        
        DB-->>CS: Committed
        CS-->>API: Success
        API-->>FE: 200 OK
        FE-->>User: Show success toast
    else Validation fails
        Schema-->>API: ValidationError
        API-->>FE: 422 Unprocessable Entity
        FE-->>User: Show error
    end
```

---

## Custom Workflow DAG Execution

This sequence details how custom workflows with parallel execution branches are processed by the Dynamic Planner.

```mermaid
sequenceDiagram
    participant WS as WorkflowService
    participant DB as PostgreSQL
    participant DP as DynamicPlanner
    participant LG as LangGraph

    WS->>DB: SELECT FROM workflows WHERE id=workflow_id
    DB-->>WS: Workflow {nodes: [...], edges: [...]}
    WS->>WS: Inject custom_workflow_steps into state

    LG->>DP: __call__(state)
    DP->>DP: Detect custom_workflow_steps in state

    DP->>DP: Parse DAG structure
    Note over DP: nodes = [{id, data: {agentId}}]
    Note over DP: edges = [{source, target}]

    DP->>DP: For each node, check are_dependencies_met()
    
    Note over DP: Dependencies met when all<br/>incoming edge sources are<br/>in executed_agents set

    DP->>DP: Collect next_agents_to_run[]
    
    alt Multiple agents ready
        DP-->>LG: {next_node: ["agent_a", "agent_b"]}
        Note over LG: LangGraph executes in parallel
        LG->>LG: Fan-out to parallel branches
        LG->>LG: Execute agent_a and agent_b concurrently
        LG->>LG: Merge results via Annotated reducers
        LG->>DP: Return to planner with merged state
    else Single agent ready
        DP-->>LG: {next_node: "agent_c"}
        LG->>LG: Execute agent_c
        LG->>DP: Return to planner
    else No agents ready (all executed)
        DP-->>LG: {next_node: "__end__"}
    end
```

---

<p align="center">
  <a href="README.md">Backend README</a> &#8226;
  <a href="CLASS_DIAGRAM.md">Class Diagrams</a> &#8226;
  <a href="SOLID_PRINCIPLES.md">SOLID</a> &#8226;
  <a href="RELIABILITY.md">Reliability</a> &#8226;
  <a href="AGENTIC_FLOW.md">Agentic Flow</a> &#8226;
  <a href="LLD_ARCHITECTURE.md">LLD</a> &#8226;
  <a href="APPLICATION_FLOW.md">App Flow</a>
</p>