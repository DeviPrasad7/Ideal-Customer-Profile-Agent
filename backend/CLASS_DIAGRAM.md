# 🧬 Enterprise Class Architecture & LLD

<div align="center">
  <img src="https://img.shields.io/badge/Architecture-Domain%20Driven%20Design-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Typing-Strict-success?style=for-the-badge" />
</div>

Welcome to the definitive guide on the Low-Level Design (LLD) and Class Architecture of the ICP-X backend. We don't just write scripts—we engineer scalable, decoupled, and highly cohesive domain models.

---

## 🏗️ The Domain Layer

Our architecture is heavily decoupled, utilizing Abstract Base Classes (ABCs) in Python and strict Dependency Injection. This ensures maximum testability, interchangeability, and absolute separation of concerns. The core of our agentic system revolves around the `BaseAgent` abstraction.

### Comprehensive Class Diagram

The following Mermaid diagram illustrates the intricate relationships, inheritance, and interfaces powering our cognitive engine.

```mermaid
classDiagram
    direction TB
    
    %% Core Abstractions
    class BaseAgent {
        <<abstract>>
        +id: UUID
        +name: str
        +invoke(state: AgentState) AgentState
        #_pre_process(state: AgentState)
        #_post_process(state: AgentState)
    }

    class ITool {
        <<interface>>
        +execute(payload: dict) Result
    }

    class IStorage {
        <<interface>>
        +save(key: str, data: dict)
        +load(key: str) dict
    }

    %% Concrete Implementations
    class EnrichmentAgent {
        -scraper_service: IScraper
        -cache: ICache
        +invoke(state: AgentState) AgentState
    }

    class ScoringAgent {
        -llm_client: ILLMClient
        -icp_model: ICPProfile
        +invoke(state: AgentState) AgentState
    }
    
    class WebScraperTool {
        +execute(payload: dict) Result
    }
    
    class PostgresStorage {
        -pool: ConnectionPool
        +save(key: str, data: dict)
        +load(key: str) dict
    }

    %% Orchestration
    class AgentOrchestrator {
        -registry: AgentRegistry
        -graph: StateGraph
        +build_graph() CompiledGraph
        +execute(input: dict) Result
    }
    
    class AgentRegistry {
        -agents: Map~str, BaseAgent~
        +register(name: str, agent: BaseAgent)
        +get(name: str) BaseAgent
    }

    %% Relationships
    BaseAgent <|-- EnrichmentAgent : Inherits
    BaseAgent <|-- ScoringAgent : Inherits
    ITool <|.. WebScraperTool : Implements
    IStorage <|.. PostgresStorage : Implements
    
    AgentOrchestrator --> AgentRegistry : Manages
    AgentRegistry o-- BaseAgent : Contains
    EnrichmentAgent --> ITool : Utilizes
    AgentOrchestrator --> IStorage : Persists State
```

---

## 🧩 Architectural Highlights

### 1. **Dependency Injection (DI)**
Every concrete implementation (like `PostgresStorage` or `WebScraperTool`) is injected into the high-level agents at runtime. The `EnrichmentAgent` never knows *how* data is scraped; it merely interfaces with `ITool`. This allows us to hot-swap a Puppeteer scraper for a Playwright scraper without touching the agent logic.

### 2. **State Management via `AgentState`**
Notice how `invoke()` receives and returns an `AgentState`. This is a strict, Pydantic-validated data contract. No unstructured dicts are passed around. The `AgentState` is immutable during a node's execution, guaranteeing side-effect-free transitions.

### 3. **The Orchestrator Hub**
The `AgentOrchestrator` is the central brain. It dynamically resolves dependencies via the `AgentRegistry` and compiles the LangGraph state machine. It abstracts away the complexity of the LangGraph runtime, exposing a clean `execute()` method to our FastAPI controllers.

---
🔙 **[Back to Backend Hub](./README.md)**
