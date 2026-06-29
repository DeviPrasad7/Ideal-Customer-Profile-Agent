# 🌊 End-to-End Application Flow & Sequences

<div align="center">
  <img src="https://img.shields.io/badge/Flow-Deterministic-009688?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Scale-Planetary-blue?style=for-the-badge" />
</div>

Understanding how a request travels through ICP-X is crucial. We have designed an **asynchronous, non-blocking, event-driven pipeline** that can handle thousands of concurrent prospect evaluations without breaking a sweat.

---

## 🚀 The Global Sequence

When a client submits a batch of prospects, the system orchestrates a symphony of API gateways, message queues, agent nodes, and database transactions.

### Macro Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Gateway
    participant Queue as Redis Queue (Async)
    participant Orchestrator as LangGraph Engine
    participant Scrapers as Enrichment Swarm
    participant LLM as GPT-4 / Claude
    participant DB as Distributed PostgreSQL

    Client->>API: POST /api/v1/prospects (Batch Payload)
    activate API
    API->>DB: Persist Initial State (Status: PENDING)
    API->>Queue: Enqueue Evaluation Job
    API-->>Client: 202 Accepted (Job ID returned instantly)
    deactivate API
    
    note over Queue, Orchestrator: Asynchronous Worker Pool takes over
    
    Queue->>Orchestrator: Dequeue & Trigger ICP Workflow
    activate Orchestrator
    
    Orchestrator->>Scrapers: Dispatch Parallel Scraping Tasks
    activate Scrapers
    Scrapers-->>Orchestrator: Return Enriched Profile Data
    deactivate Scrapers
    
    Orchestrator->>DB: Checkpoint Graph State
    
    Orchestrator->>LLM: Evaluate against ICP Criteria
    activate LLM
    LLM-->>Orchestrator: Return Structured Score & Confidence
    deactivate LLM
    
    alt Confidence < Threshold (Requires Human)
        Orchestrator->>DB: Update State to HITL_REQUIRED
        Orchestrator-->>Queue: Suspend Execution (Hibernate)
        
        Client->>API: POST /api/v1/intervene (Human Decision)
        API->>Queue: Enqueue Resume Signal
        Queue->>Orchestrator: Wake Up & Resume from Checkpoint
    end
    
    Orchestrator->>DB: Finalize Profile State (QUALIFIED/REJECTED)
    deactivate Orchestrator
    
    note over DB, Client: Webhook or Polling retrieves final state
```

---

## 🔍 Deep Dive: The API Gateway

The FastAPI layer acts purely as a highly optimized traffic cop. It performs synchronous schema validation via Pydantic V2 (written in Rust) and immediately offloads heavy lifting to the background queue. This ensures that our HTTP response times remain consistently under 50ms, regardless of LLM latency.

## 🔄 Checkpointing & Resumption

Notice Step 6 in the diagram (`Checkpoint Graph State`). This is where the magic happens. Because we checkpoint the entire execution graph to PostgreSQL, the system is entirely resilient to worker crashes. If a Kubernetes pod dies during Step 7 (LLM evaluation), a new pod will wake up, read the checkpoint, and resume *exactly* at Step 7 without re-running the scrapers.

---
🔙 **[Back to Backend Hub](./README.md)**
