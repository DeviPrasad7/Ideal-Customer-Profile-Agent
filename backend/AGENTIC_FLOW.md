<h1 align="center">Agentic Flow Architecture</h1>

<p align="center">
  <strong>Complete documentation of the agentic workflow system -- from dynamic LLM-powered planning and state management through parallel agent execution, custom workflow DAG processing, and the full agent lifecycle.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Orchestration-LangGraph-FF6F00?style=for-the-badge" alt="LangGraph">
  <img src="https://img.shields.io/badge/Agents-16_Specialized_Nodes-9C27B0?style=for-the-badge" alt="Agents">
  <img src="https://img.shields.io/badge/Planning-LLM_Powered-2196F3?style=for-the-badge" alt="Planning">
  <img src="https://img.shields.io/badge/Execution-Parallel_DAG-4CAF50?style=for-the-badge" alt="Parallel">
  <img src="https://img.shields.io/badge/HITL-Interrupt_Based-E91E63?style=for-the-badge" alt="HITL">
</p>

---

## Table of Contents

- [Agentic Architecture Overview](#agentic-architecture-overview)
- [The Dynamic Planner -- Brain of the System](#the-dynamic-planner----brain-of-the-system)
- [Agent Lifecycle and State Flow](#agent-lifecycle-and-state-flow)
- [GraphState -- The Shared Memory Bus](#graphstate----the-shared-memory-bus)
- [Parallel Execution and Fan-Out](#parallel-execution-and-fan-out)
- [Custom Workflow DAG Processing](#custom-workflow-dag-processing)
- [Custom Agent Creation and Execution](#custom-agent-creation-and-execution)
- [Human-in-the-Loop Interrupt Model](#human-in-the-loop-interrupt-model)
- [Agent Registration and Discovery](#agent-registration-and-discovery)
- [Standard Pipeline Sequence](#standard-pipeline-sequence)
- [Agent Communication Patterns](#agent-communication-patterns)

---

## Agentic Architecture Overview

The ICP Agent platform implements a **hub-and-spoke agent orchestration model** powered by LangGraph's `StateGraph`. At the center sits the `DynamicPlannerNode` -- an LLM-powered orchestrator that inspects the current state and decides which agent to execute next. All worker agents execute their specialized task and return to the planner for the next routing decision.

```mermaid
graph TB
    START["START"] --> DP

    subgraph Hub["Dynamic Planner (Hub)"]
        DP["DynamicPlannerNode<br/>LLM-Powered Router"]
    end

    subgraph Spokes["Specialized Agent Fleet (Spokes)"]
        RES["ResearcherNode<br/>Web Research"]
        ENR["EnricherNode<br/>Firmographics"]
        TSK["TechStackDetectorNode<br/>Technology Analysis"]
        SCR["ScoreNode<br/>ICP Scoring"]
        CV["CrossValidatorNode<br/>Data Validation"]
        PM["PersonaMatcherNode<br/>Buyer Matching"]
        CF["ContactFinderNode<br/>Decision Makers"]
        CI["CompetitorIntelNode<br/>Competitive Landscape"]
        OG["OutreachGeneratorNode<br/>Email Drafts"]
        SUM["SummarizerNode<br/>Executive Summary"]
        MON["MonitorNode<br/>Metrics Collection"]
        DAE["DynamicAgentExecutorNode<br/>Custom Agents"]
        CON["ConsolidationNode<br/>Data Merging"]
        END_NODE["EnderNode<br/>Cleanup"]
    end

    subgraph Terminal["Terminal Nodes"]
        HITL["HitlGatewayNode<br/>Human Review"]
        OD["OutputDispatcherNode<br/>Final Dispatch"]
    end

    DP -->|routes to| RES & ENR & TSK & SCR & CV & PM & CF & CI & OG & SUM & MON & DAE & CON & END_NODE
    DP -->|routes to| HITL
    
    RES & ENR & TSK & SCR & CV & PM & CF & CI & OG & SUM & MON & DAE & CON & END_NODE -->|return to| DP
    
    HITL -->|approved| OD
    OD --> FINISH["END"]
    DP -->|"__end__"| FINISH
```

This architecture enables several critical capabilities:

- **Adaptive routing** -- The planner can choose different paths based on what data has been gathered
- **Graceful skip** -- If an agent fails, the planner can route around it
- **Dynamic ordering** -- The execution order is not hardcoded; it adapts to each prospect
- **Parallel dispatch** -- The planner can send multiple agents simultaneously when their dependencies are satisfied

---

## The Dynamic Planner -- Brain of the System

The `DynamicPlannerNode` implements a **three-tier routing strategy** that ensures the pipeline always makes forward progress:

```mermaid
graph TB
    ENTRY["DynamicPlanner.__call__(state)"]
    
    CHECK_STATUS{"overall_status in<br/>terminal states?"}
    END_EARLY["Return __end__"]
    
    CHECK_APPROVED{"status == APPROVED?"}
    DISPATCH["Return output_dispatcher_node"]
    
    CHECK_SIM{"simulate_failure?"}
    FORCE_RETRY["Force retry on last_agent"]
    
    CHECK_CUSTOM{"custom_workflow_steps<br/>attached?"}
    
    subgraph Tier1["Tier 1: Custom Workflow DAG"]
        DAG["Parse DAG topology"]
        DEPS["Check dependency satisfaction"]
        PARALLEL["Dispatch ready agents"]
    end
    
    subgraph Tier2["Tier 2: LLM-Powered Routing"]
        PROMPT["Construct routing prompt"]
        LLM["Call LLM (strategy: fast)"]
        VALIDATE["Validate response"]
        ROUTE["Route to selected agent"]
    end
    
    subgraph Tier3["Tier 3: Deterministic Fallback"]
        SEQ["Linear agent sequence"]
        NEXT["Next unexecuted agent"]
    end

    ENTRY --> CHECK_STATUS
    CHECK_STATUS -->|Yes| END_EARLY
    CHECK_STATUS -->|No| CHECK_APPROVED
    CHECK_APPROVED -->|Yes| DISPATCH
    CHECK_APPROVED -->|No| CHECK_SIM
    CHECK_SIM -->|Yes| FORCE_RETRY
    CHECK_SIM -->|No| CHECK_CUSTOM
    CHECK_CUSTOM -->|Yes| Tier1
    CHECK_CUSTOM -->|No| Tier2
    Tier2 -->|LLM fails| Tier3
```

### Tier 1: Custom Workflow DAG Routing

When a custom workflow is attached, the planner performs **topological traversal** of the DAG:

1. Parse the DAG into `nodes[]` and `edges[]`
2. For each node, check if all incoming edge sources exist in `executed_agents`
3. Collect all nodes whose dependencies are satisfied
4. Dispatch them as a parallel list: `{next_node: ["agent_a", "agent_b"]}`

### Tier 2: LLM-Powered Intelligent Routing

When no custom workflow is present, the planner constructs a context-aware prompt:

```
You are a B2B sales workflow planner.
Status: PENDING
Executed: [researcher_node, enricher_node]
Data Gathered: {firmographics: {name: "Acme", ...}, tech_stack: [...]}

Agents:
[{"name": "score_node", "desc": "Scores the company against ICP..."}, ...]

Rules:
- Choose the best next agent based on missing data.
- Once firmographic & tech stack data exist, do cross_validator_node...
- Return ONLY JSON: {"reasoning": "...", "next_node": "agent_name"}
```

The response is parsed, validated against the registry, and used for routing.

### Tier 3: Deterministic Fallback

If the LLM fails or returns an invalid response, the planner falls back to a simple linear sequence of all registered agents, executing the first unexecuted one.

---

## Agent Lifecycle and State Flow

Each agent follows a standardized lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Registered: @register_agent decorator

    Registered --> Instantiated: setup_graph()
    Instantiated --> Wrapped: SafeAgentWrapper
    Wrapped --> Idle: Added to StateGraph

    Idle --> Selected: DynamicPlanner routes
    Selected --> Executing: __call__(state)
    
    Executing --> Success: Returns state delta
    Executing --> Failed: Throws exception

    Success --> Traced: Wrapper records trace
    Failed --> Caught: Wrapper catches exception
    Caught --> Traced: Error recorded in state

    Traced --> Idle: Returns to planner

    Note right of Registered: Agent class stored in AgentRegistry
    Note right of Wrapped: Fault isolation + tracing added
    Note right of Traced: execution_trace updated
```

### Agent Initialization Pattern

Every agent follows a consistent constructor pattern:

```python
def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
    self.toolbox = toolbox
    self.memory = memory
    self.config = config
```

This uniform constructor signature is enforced by the `setup_graph()` function, which instantiates all agents with the same three dependencies.

### Agent Return Contract

Every agent returns a dictionary containing **only the state fields it wants to update**:

```python
return {
    "executed_agents": ["enricher_node"],     # Required: mark self as executed
    "data": {"firmographics": {...}},         # Optional: add data
    "confidence_score": 0.85,                 # Optional: update score
    "recent_thoughts": ["Extracted data..."]  # Optional: add thoughts
}
```

The `Annotated` reducers in `GraphState` handle merging these partial updates with the existing state.

---

## GraphState -- The Shared Memory Bus

The `GraphState` serves as the **central data bus** for the entire agentic workflow:

```mermaid
graph TB
    subgraph State["GraphState (TypedDict)"]
        subgraph Identity["Identity"]
            PID["prospect_id: str"]
            TRIGGER["current_trigger_event: str"]
        end

        subgraph Config["Configuration"]
            CFG["config: dict<br/>(icp, persona, thresholds)"]
        end

        subgraph Data["Accumulated Data (Annotated[dict, add_dict])"]
            D["data: dict<br/>firmographics, tech_stack,<br/>contacts, outreach_drafts,<br/>summary_object, ..."]
        end

        subgraph Validation["Validation"]
            VN["validation_notes: Annotated[list, add_list]"]
            CS["confidence_score: float"]
            HC["has_conflict: bool"]
        end

        subgraph Routing["Routing Control"]
            EA["executed_agents: Annotated[list, add_list]"]
            DA["dispatched_agents: Annotated[list, add_list]"]
            ERR["errors: Annotated[list, add_list]"]
            RC["retry_counts: Annotated[dict, add_dict]"]
            NN["next_node: str | list[str]"]
            LA["last_agent: str"]
        end

        subgraph HITL["Human Override"]
            HOP["human_override_payload: str"]
            OS["overall_status: str"]
        end

        subgraph Custom["Custom Workflow"]
            CWS["custom_workflow_steps: dict | list | None"]
            CWI["custom_workflow_id: str"]
            NCA["next_custom_agent: str"]
        end

        subgraph Trace["Observability"]
            RT["recent_thoughts: Annotated[list, add_list]"]
            ET["execution_trace: Annotated[list, add_list]"]
        end
    end
```

### Annotated Reducer Functions

The `Annotated` types use custom reducer functions to safely merge state updates from parallel branches:

```mermaid
graph LR
    subgraph Parallel["Parallel Execution"]
        A["Agent A returns:<br/>data = {tech_stack: [...]}"]
        B["Agent B returns:<br/>data = {firmographics: {...}}"]
    end

    subgraph Reducer["add_dict Reducer"]
        MERGE["Merged result:<br/>data = {<br/>  tech_stack: [...],<br/>  firmographics: {...}<br/>}"]
    end

    A --> MERGE
    B --> MERGE
```

| Reducer | Behavior | Used For |
|:---|:---|:---|
| `add_dict` | Merges dictionaries (`{**left, **right}`) | `data`, `retry_counts`, `config` |
| `add_list` | Concatenates lists (`left + right`) | `executed_agents`, `errors`, `validation_notes`, `recent_thoughts`, `execution_trace` |

This eliminates race conditions when multiple agents execute concurrently.

---

## Parallel Execution and Fan-Out

The `DynamicPlannerNode` supports parallel agent dispatch when processing custom workflow DAGs:

```mermaid
graph TB
    DP["DynamicPlanner"]
    
    DP -->|"next_node: ['researcher_node', 'enricher_node']"| FAN["LangGraph Fan-Out"]
    
    FAN --> RES["ResearcherNode"]
    FAN --> ENR["EnricherNode"]
    
    RES -->|"data: {market_context: ...}"| MERGE["LangGraph Merge<br/>(Annotated Reducers)"]
    ENR -->|"data: {firmographics: ...}"| MERGE
    
    MERGE -->|Merged state| DP2["DynamicPlanner<br/>(next iteration)"]
```

When the planner returns `next_node` as a list, LangGraph automatically:
1. Forks execution into parallel branches
2. Executes each agent concurrently
3. Merges the results using the `Annotated` reducers
4. Returns the merged state to the planner

This enables significant performance improvements for independent data gathering tasks.

---

## Custom Workflow DAG Processing

Users can design custom agent pipelines using the Workflow Studio frontend. These DAGs are stored in the `workflows` table and loaded at runtime.

### DAG Structure

```python
{
    "nodes": [
        {"id": "1", "data": {"agentId": "researcher_node"}},
        {"id": "2", "data": {"agentId": "enricher_node"}},
        {"id": "3", "data": {"agentId": "score_node"}}
    ],
    "edges": [
        {"source": "1", "target": "3"},  # researcher -> score
        {"source": "2", "target": "3"}   # enricher -> score
    ]
}
```

### Dependency Resolution Algorithm

```mermaid
graph TB
    START["For each node in DAG"]
    CHECK["Get incoming edges"]
    DEPS{"All source nodes<br/>in executed_agents?"}
    READY["Add to next_agents_to_run"]
    SKIP["Skip (dependencies not met)"]
    
    DISPATCH{"next_agents_to_run empty?"}
    ALL_DONE{"All valid agents executed?"}
    END_WF["Return __end__"]
    WAIT["Return empty (waiting)"]
    PARALLEL["Return list of agents"]

    START --> CHECK
    CHECK --> DEPS
    DEPS -->|Yes| READY
    DEPS -->|No| SKIP
    READY --> DISPATCH
    SKIP --> DISPATCH
    DISPATCH -->|Yes| ALL_DONE
    DISPATCH -->|No| PARALLEL
    ALL_DONE -->|Yes| END_WF
    ALL_DONE -->|No| WAIT
```

### Topological Execution Example

```mermaid
graph LR
    subgraph Step1["Step 1: No dependencies"]
        R["Researcher"]
        E["Enricher"]
    end

    subgraph Step2["Step 2: R and E complete"]
        S["Score"]
    end

    subgraph Step3["Step 3: S complete"]
        SUM["Summarizer"]
    end

    R --> S
    E --> S
    S --> SUM
```

- **Step 1:** Researcher and Enricher have no incoming edges -- dispatched in parallel
- **Step 2:** Score has edges from both Researcher and Enricher -- waits until both complete
- **Step 3:** Summarizer has an edge from Score -- dispatched after Score completes

---

## Custom Agent Creation and Execution

### Agent Definition Model

```mermaid
graph TB
    subgraph Definition["Custom Agent Definition (DB)"]
        NAME["name: 'competitive_analyst'"]
        DESC["description: 'Analyzes...'"]
        PROMPT["system_prompt: 'You are...'"]
        TOOLS["allowed_tools: ['WebSearch', 'Crunchbase']"]
    end

    subgraph Execution["Runtime Execution"]
        LOAD["Load from custom_agents table"]
        BUILD["Build ReAct agent with tools"]
        RUN["Execute with state data"]
        STORE["Store output in state"]
    end

    Definition --> LOAD
    LOAD --> BUILD
    BUILD --> RUN
    RUN --> STORE
```

### Execution Modes

```mermaid
graph TB
    EXECUTOR["DynamicAgentExecutor"]
    
    TOOLS{"Agent has tools?"}
    
    subgraph ReAct["ReAct Agent Mode"]
        BUILD["create_react_agent(llm, tools, system_prompt)"]
        INVOKE["ainvoke({messages: [task + data]})"]
        LOOP["Autonomous tool selection loop"]
    end

    subgraph Simple["Simple Generation Mode"]
        GEN["generate_text(system_prompt + data)"]
    end

    EXECUTOR --> TOOLS
    TOOLS -->|Yes| ReAct
    TOOLS -->|No| Simple
```

When tools are enabled, the executor builds a **ReAct agent** (Reasoning + Acting) that can autonomously decide which tools to call:

1. The LLM reads the system prompt and current state data
2. It decides which tool to call (WebSearch, Crunchbase, LinkedIn, EmployeeSearch)
3. The tool executes and returns results
4. The LLM observes the results and decides whether to call another tool or return a final answer

---

## Human-in-the-Loop Interrupt Model

### Interrupt Decision Logic

```mermaid
graph TB
    ENTRY["HitlGatewayNode.__call__(state)"]
    
    WEBSITE{"website_url<br/>exists?"}
    MISSING["HITL: Missing website"]
    
    CONF{"confidence >= threshold?"}
    LOW["HITL: Low confidence"]
    
    CONFLICT{"has_conflict?"}
    CONFLICT_HITL["HITL: Data conflict"]
    
    SUMMARY{"summary_object<br/>exists?"}
    
    AUTO{"confidence >= auto_threshold?"}
    AUTO_APPROVE["Auto-approve<br/>(no human needed)"]
    FINAL_REVIEW["HITL: Final review"]

    ENTRY --> WEBSITE
    WEBSITE -->|No| MISSING
    WEBSITE -->|Yes| CONF
    CONF -->|No| LOW
    CONF -->|Yes| CONFLICT
    CONFLICT -->|Yes| CONFLICT_HITL
    CONFLICT -->|No| SUMMARY
    SUMMARY -->|No| ENTRY_END["Continue pipeline"]
    SUMMARY -->|Yes| AUTO
    AUTO -->|Yes| AUTO_APPROVE
    AUTO -->|No| FINAL_REVIEW
```

### Interrupt and Resume Mechanism

```mermaid
sequenceDiagram
    participant HITL as HitlGatewayNode
    participant LG as LangGraph
    participant WS as WorkflowService
    participant DB as PostgreSQL
    participant User as Human Reviewer
    
    HITL->>LG: interrupt({prospect_id, reason, state})
    Note over LG: Execution FREEZES here
    LG->>WS: State snapshot with interrupts
    WS->>DB: Create HITL request
    WS->>DB: Set status = PENDING_HUMAN
    
    Note over User: Time passes (up to 24h)
    
    User->>WS: Approve/Reject/Edit
    WS->>LG: Command(resume={action, edits})
    LG->>HITL: Resume with response
    
    Note over HITL: Execution CONTINUES from freeze point
    
    HITL->>HITL: Process response
    HITL-->>LG: {overall_status: "APPROVED", data: edits}
```

The key insight is that LangGraph's `interrupt()` function **freezes the entire execution context**, including the call stack. When resumed, execution continues from the exact line after the `interrupt()` call, with the resume payload available as the return value.

---

## Agent Registration and Discovery

### Registration Flow

```mermaid
graph LR
    subgraph Development["Development Time"]
        DEV["Write agent class"]
        DEC["Apply @register_agent decorator"]
    end

    subgraph Import["Import Time"]
        INIT["agents/__init__.py imports all agents"]
        REG["Each decorator calls registry.register()"]
        STORE["AgentRegistry stores class + description"]
    end

    subgraph Runtime["Runtime"]
        GRAPH["setup_graph() iterates registry"]
        WRAP["SafeAgentWrapper wraps each agent"]
        WIRE["Conditional edges auto-wired"]
        PLAN["Planner queries registry for available agents"]
    end

    DEV --> DEC --> INIT --> REG --> STORE --> GRAPH --> WRAP --> WIRE --> PLAN
```

The `agents/__init__.py` file imports all agent modules, triggering their `@register_agent` decorators. This is the only "manual" step -- and it's a standard Python import.

---

## Standard Pipeline Sequence

The typical execution sequence for a prospect follows this order (though the LLM planner may adapt based on data):

```mermaid
graph LR
    1["Researcher<br/>Market context"] --> 2["Enricher<br/>Firmographics"]
    2 --> 3["TechStack<br/>Technologies"]
    3 --> 4["Score<br/>ICP matching"]
    4 --> 5["CrossValidator<br/>Data integrity"]
    5 --> 6["PersonaMatcher<br/>Buyer profiles"]
    6 --> 7["ContactFinder<br/>Decision makers"]
    7 --> 8["CompetitorIntel<br/>Competitors"]
    8 --> 9["OutreachGen<br/>Email drafts"]
    9 --> 10["Summarizer<br/>Executive summary"]
    10 --> 11["HITL Gateway<br/>Human review"]
    11 --> 12["Output<br/>Final dispatch"]
```

---

## Agent Communication Patterns

Agents communicate exclusively through the shared `GraphState`. There is no direct agent-to-agent communication:

```mermaid
graph TB
    subgraph Pattern["Communication via Shared State"]
        A["Agent A writes:<br/>data.firmographics = {...}"]
        STATE["GraphState<br/>(Shared Memory Bus)"]
        B["Agent B reads:<br/>state['data']['firmographics']"]
    end

    A -->|"writes"| STATE
    STATE -->|"reads"| B
```

This pattern provides:
- **Loose coupling** -- Agents don't know about each other
- **Replay capability** -- The state is checkpointed, enabling replay
- **Observability** -- All agent outputs are visible in the state
- **Testability** -- Any agent can be tested with a mock state dict

---

<p align="center">
  <a href="README.md">Backend README</a> &#8226;
  <a href="CLASS_DIAGRAM.md">Class Diagrams</a> &#8226;
  <a href="SEQUENCE_FLOW.md">Sequence Flows</a> &#8226;
  <a href="SOLID_PRINCIPLES.md">SOLID</a> &#8226;
  <a href="RELIABILITY.md">Reliability</a> &#8226;
  <a href="LLD_ARCHITECTURE.md">LLD</a> &#8226;
  <a href="APPLICATION_FLOW.md">App Flow</a>
</p>