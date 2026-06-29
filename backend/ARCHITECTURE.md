# 🏛️ System Architecture & Agentic Flow

This document details the macro-architecture of the ICP-X backend. We employ a **Reactive, Event-Driven Agentic Architecture** that redefines how background processing and AI orchestration should be built.

---

## 🌊 The Agentic Lifecycle (Sequence Diagram)

When a prospect enters the system, they don't just get saved to a database. They are pushed into an intelligent pipeline orchestrated by LangGraph.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Gateway
    participant Graph as LangGraph Orchestrator
    participant Enrich as Enrichment Swarm
    participant LLM as Evaluator Agent
    participant DB as PostgreSQL

    Client->>API: POST /prospects (Batch)
    API->>DB: Persist Initial State (PENDING)
    API-->>Client: 202 Accepted (Job ID)
    
    API->>Graph: Trigger ICP Workflow
    activate Graph
    Graph->>Enrich: Dispatch Scraping Tasks
    activate Enrich
    Enrich-->>Graph: Return Enriched Profile
    deactivate Enrich
    
    Graph->>DB: Checkpoint State
    
    Graph->>LLM: Evaluate against ICP Criteria
    activate LLM
    LLM-->>Graph: Return Score & Confidence
    deactivate LLM
    
    alt Confidence < Threshold
        Graph->>DB: Update State to HITL_REQUIRED
        Graph-->>API: Yield execution (Pause)
        Client->>API: POST /intervene (Human Approval)
        API->>Graph: Resume Workflow with Input
    end
    
    Graph->>DB: Finalize Profile State (QUALIFIED/REJECTED)
    deactivate Graph
```

---

## 🤖 Dynamic Graph Routing

Our agentic flow isn't a static pipeline; it's a dynamic, cyclic graph capable of self-reflection and recursive enhancement.

```mermaid
stateDiagram-v2
    [*] --> Ingestion
    Ingestion --> Enrichment : New Prospect
    
    state Enrichment {
        [*] --> WebScraping
        WebScraping --> APIEnrichment
        APIEnrichment --> Validation
        Validation --> WebScraping : Missing Data (Retry)
        Validation --> [*] : Data Sufficient
    }
    
    Enrichment --> Scoring
    Scoring --> HITL : Low Confidence
    HITL --> Scoring : Human Feedback
    Scoring --> Routing : High Confidence
    
    Routing --> [*]
```

---

## 🛡️ Enterprise Reliability Engineering

Our architecture guarantees zero data loss and uninterrupted service:

1. **State Checkpointing**: LangGraph implicitly checkpoints state after *every* node transition to PostgreSQL. If the server crashes, the workflow resumes exactly where it left off.
2. **Circuit Breakers**: External API calls (LLMs, scrapers) are wrapped in resilient circuit breakers to prevent cascading failures.
3. **Dead Letter Queues (DLQ)**: Poison pill payloads that cause unhandled exceptions are safely routed to a DLQ for manual inspection, ensuring the main processing queue never blocks.

---
🔙 **[Back to Backend Hub](./README.md)** | 📐 **[Next: Low-Level Design (LLD)](./LLD.md)**
