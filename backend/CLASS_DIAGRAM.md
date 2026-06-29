<h1 align="center">Class Diagram Reference</h1>

<p align="center">
  <strong>Complete UML class diagrams documenting inheritance hierarchies, protocol interfaces, composition relationships, and the structural backbone of the ICP Agent platform.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Diagrams-Mermaid_UML-8A2BE2?style=for-the-badge" alt="Mermaid">
  <img src="https://img.shields.io/badge/Patterns-GoF_Compliant-4CAF50?style=for-the-badge" alt="GoF">
  <img src="https://img.shields.io/badge/Interfaces-Protocol_Typed-2196F3?style=for-the-badge" alt="Protocol">
</p>

---

## Table of Contents

- [Agent Layer Class Hierarchy](#agent-layer-class-hierarchy)
- [Service Layer Class Structure](#service-layer-class-structure)
- [Data Layer and ORM Models](#data-layer-and-orm-models)
- [Core Infrastructure Classes](#core-infrastructure-classes)
- [API Provider Framework](#api-provider-framework)
- [Toolbox Facade Composition](#toolbox-facade-composition)
- [Complete System Class Map](#complete-system-class-map)

---

## Agent Layer Class Hierarchy

The agent layer is the heart of the orchestration engine. It is built around the `AgentNode` Protocol -- a formal interface contract that every agent must satisfy. The `SafeAgentWrapper` decorator provides fault isolation, execution tracing, and retry tracking without modifying agent implementation code.

### AgentNode Protocol and SafeAgentWrapper

```mermaid
classDiagram
    class AgentNode {
        <<Protocol>>
        +__call__(state: GraphState) Dict~str, Any~
    }

    class AgentConfig {
        <<TypedDict>>
        +icp: Dict~str, Any~
        +personas: Dict~str, Any~
    }

    class SafeAgentWrapper {
        -agent: AgentNode
        -agent_name: str
        +__init__(agent: AgentNode, agent_name: str)
        +__call__(state: GraphState) Dict~str, Any~
        -_record_trace(result: dict, start: float, end: float) dict
        -_handle_failure(state: GraphState, error: Exception) dict
    }

    class AgentRegistry {
        -_agents: Dict~str, Type~
        -_descriptions: Dict~str, str~
        +register(cls: Type, name: str, description: str) None
        +get_agent(name: str) Type
        +list_agents() List~str~
        +list_agents_with_descriptions() List~dict~
        +get_description(name: str) str
    }

    AgentNode <|.. SafeAgentWrapper : wraps
    AgentRegistry o-- AgentNode : manages
    SafeAgentWrapper --> AgentNode : delegates to
```

**Design Rationale:** The `AgentNode` Protocol uses Python's structural subtyping system. Any class that implements `async def __call__(self, state: GraphState) -> Dict[str, Any]` is considered a valid `AgentNode` without explicit inheritance. This enables maximum flexibility -- agents don't need to inherit from a base class, and third-party agent implementations can be integrated without modification.

The `SafeAgentWrapper` implements the **Decorator Pattern** (GoF), adding cross-cutting concerns (fault isolation, tracing, retry tracking) to any agent without modifying its source code. This is a textbook application of the Open/Closed Principle -- the wrapper is open for extension but closed for modification.

### Agent Fleet Class Diagram

```mermaid
classDiagram
    class AgentNode {
        <<Protocol>>
        +__call__(state: GraphState) Dict~str, Any~
    }

    class DynamicPlannerNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        -registry: AgentRegistry
        +__call__(state: GraphState) Dict~str, Any~
        -_route_custom_workflow(state: GraphState) dict
        -_route_via_llm(state: GraphState) dict
        -_route_fallback(state: GraphState) dict
    }

    class ResearcherNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        -search_client: ISearchClient
        +__call__(state: GraphState) Dict~str, Any~
    }

    class EnricherNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class TechStackDetectorNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class ScoreNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class CrossValidatorNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class PersonaMatcherNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class ContactFinderNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class CompetitorIntelNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class OutreachGeneratorNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class SummarizerNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class HitlGatewayNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class OutputDispatcherNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class DynamicAgentExecutorNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class ConsolidationNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class MonitorNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    class EnderNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        +__call__(state: GraphState) Dict~str, Any~
    }

    AgentNode <|.. DynamicPlannerNode
    AgentNode <|.. ResearcherNode
    AgentNode <|.. EnricherNode
    AgentNode <|.. TechStackDetectorNode
    AgentNode <|.. ScoreNode
    AgentNode <|.. CrossValidatorNode
    AgentNode <|.. PersonaMatcherNode
    AgentNode <|.. ContactFinderNode
    AgentNode <|.. CompetitorIntelNode
    AgentNode <|.. OutreachGeneratorNode
    AgentNode <|.. SummarizerNode
    AgentNode <|.. HitlGatewayNode
    AgentNode <|.. OutputDispatcherNode
    AgentNode <|.. DynamicAgentExecutorNode
    AgentNode <|.. ConsolidationNode
    AgentNode <|.. MonitorNode
    AgentNode <|.. EnderNode
```

### Researcher Node -- Interface Segregation

The `ResearcherNode` demonstrates the **Interface Segregation Principle** with a dedicated `ISearchClient` abstraction:

```mermaid
classDiagram
    class ISearchClient {
        <<Abstract>>
        +search_company_info(company_name: str)* str
        +find_competitors(company_name: str)* List~str~
    }

    class TavilySearchClient {
        -search_tool: TavilySearchResults
        +search_company_info(company_name: str) str
        +find_competitors(company_name: str) List~str~
    }

    class ResearcherNode {
        -toolbox: Toolbox
        -memory: MemoryService
        -config: dict
        -search_client: ISearchClient
        +__call__(state: GraphState) Dict~str, Any~
    }

    ISearchClient <|-- TavilySearchClient
    ResearcherNode --> ISearchClient : depends on abstraction
```

---

## Service Layer Class Structure

The service layer implements the business logic of the platform. Every service depends on abstractions (Protocols) rather than concretions, enabling seamless testing and implementation swapping.

### Service Protocol Interfaces

```mermaid
classDiagram
    class LLMServiceProtocol {
        <<Protocol>>
        +generate_text(prompt: str, fallback: str, require_json: bool, strategy: str) str
    }

    class ScrapingServiceProtocol {
        <<Protocol>>
        +fetch_webpage(url: str, timeout_sec: int) WebPage
        +detect_tech_stack(html_content: str, domain: str) list~TechStackEntry~
        +scrape_careers_page(url: str) list~JobPosting~
    }

    class EnrichmentServiceProtocol {
        <<Protocol>>
        +fetch_crunchbase(company_name: str) CompanyProfile
        +scrape_linkedin(company_name: str) dict
        +validate_email(email: str) EmailValidationResult
        +get_competitor_info(tech_tag: str) CompetitorMapping
        +find_company_employees(company_name: str) list~dict~
        +enrich_contact(person_name: str, domain: str) dict
        +fetch_rss_entries(url: str) list~dict~
        +fetch_jobs(company: str) list~dict~
    }

    class LLMService {
        -_gemini_pool: list
        -_groq_pool: list
        -_gemini_idx: int
        -_groq_idx: int
        -_initialized: bool
        -_global_lock: asyncio.Lock
        -_global_last_call_time: float
        +get_next_llm(strategy: str) ChatModel
        +generate_text(prompt: str, fallback: str, require_json: bool, strategy: str) str
        -_ensure_initialized() None
    }

    class ScrapingService {
        -llm_service: LLMService
        +fetch_webpage(url: str, timeout_sec: int) WebPage
        +detect_tech_stack(html_content: str, domain: str) list~TechStackEntry~
        +scrape_careers_page(url: str) list~JobPosting~
        +sandbox_scrape(url: str) dict
    }

    class EnrichmentService {
        -llm_service: LLMService
        -tavily_client: AsyncTavilyClient
        +fetch_crunchbase(company_name: str) CompanyProfile
        +scrape_linkedin(company_name: str) dict
        +validate_email(email: str) EmailValidationResult
        +get_competitor_info(tech_tag: str) CompetitorMapping
        +find_company_employees(company_name: str) list~dict~
        +enrich_contact(person_name: str, domain: str) dict
        +fetch_rss_entries(url: str) list~dict~
        +fetch_jobs(company: str) list~dict~
        +sandbox_enrich(company_name: str) dict
        -_search_web(query: str) str
    }

    LLMServiceProtocol <|.. LLMService
    ScrapingServiceProtocol <|.. ScrapingService
    EnrichmentServiceProtocol <|.. EnrichmentService
```

### Service Composition

```mermaid
classDiagram
    class WorkflowService {
        -_app: CompiledGraph
        -_hitl_service: HITLService
        -_tasks: set~Task~
        +submit_prospect(state: GraphState, thread_id: str) str
        +resume_with_hitl(thread_id: str, decision: str, corrections: dict) None
        +set_hitl_service(hitl_service: HITLService) None
    }

    class MemoryService {
        -session_factory: Callable
        +has_event_been_processed(event_hash: str) bool
        +mark_event_processed(event_hash: str, prospect_id: str, status: str) bool
        +save_prospect_state(state: Any) None
        +load_prospect_state(prospect_id: str) Any
        +list_prospects(filters: dict) List~ProspectSummary~
        +create_hitl_request(prospect_id: str, summary: str) UUID
        +get_pending_hitl_requests() List~HITLRequest~
        +resolve_hitl_request_and_update_prospect(request_id: UUID, decision: str, corrections: dict) str
        +rollback_prospect_state(prospect_id: str) None
        +save_emergency_state(state: Any) None
    }

    class HITLService {
        -memory_service: MemoryService
        -workflow_service: WorkflowService
        +create_request(prospect_id: str, interrupt_data: dict) UUID
        +resolve_request(request_id: str, decision: str, corrections: dict) None
    }

    class ConfigService {
        -session: AsyncSession
        +get_icp() ICPCriteria
        +update_icp(criteria: ICPCriteria) None
        +get_persona() PersonaDefinition
        +update_persona(persona: PersonaDefinition) None
        +get_thresholds() ThresholdConfig
        +update_thresholds(thresholds: ThresholdConfig) None
        +reset_to_defaults() None
        -_load_defaults() dict
        -_get_config(key: str, schema: type, default_key: str) BaseModel
        -_update_config(key: str, value: dict) None
    }

    class TriggerMonitor {
        -toolbox: Toolbox
        -workflow_service: WorkflowService
        -provider_factory: APIProviderFactory
        -_running: bool
        -_task: asyncio.Task
        -_last_polled: dict
        +start() None
        +stop() None
        +poll_sources() None
        -_poll_loop() None
        -_cleanup_orphaned_events() None
    }

    WorkflowService --> HITLService : delegates HITL
    HITLService --> MemoryService : persists state
    HITLService --> WorkflowService : resumes workflow
    TriggerMonitor --> WorkflowService : submits prospects
```

---

## Data Layer and ORM Models

### SQLAlchemy ORM Model Hierarchy

```mermaid
classDiagram
    class Base {
        <<SQLAlchemy Declarative Base>>
    }

    class Prospect {
        +id: UUID [PK]
        +display_id: String [Index]
        +company_name: String [Index]
        +website: String
        +status: String [Index]
        +state_json: JSON
        +created_at: DateTime
        +updated_at: DateTime
        +workflow_thread_id: String
        +custom_workflow_id: UUID [FK]
        +hitl_requests: Relationship
    }

    class HITLRequest {
        +id: UUID [PK]
        +display_id: String [Index]
        +prospect_id: UUID [FK]
        +summary: String
        +decision: String [Index]
        +corrections: JSON
        +created_at: DateTime
        +resolved_at: DateTime
        +prospect: Relationship
    }

    class CustomAgent {
        +id: UUID [PK]
        +name: String [Index]
        +description: String
        +system_prompt: String
        +allowed_tools: JSON
        +created_at: DateTime
    }

    class Workflow {
        +id: UUID [PK]
        +name: String [Index]
        +description: String
        +steps: JSON
        +created_at: DateTime
    }

    class Config {
        +key: String [PK]
        +value: JSON
        +updated_at: DateTime
    }

    class TriggerSource {
        +id: UUID [PK]
        +type: String
        +url: String
        +interval_seconds: Integer
        +enabled: Boolean
        +config: JSON
        +created_at: DateTime
    }

    class ProcessedEvent {
        +event_hash: String [PK]
        +prospect_id: String
        +status: String
        +processed_at: DateTime
    }

    Base <|-- Prospect
    Base <|-- HITLRequest
    Base <|-- CustomAgent
    Base <|-- Workflow
    Base <|-- Config
    Base <|-- TriggerSource
    Base <|-- ProcessedEvent

    Prospect "1" --> "*" HITLRequest : has many
    Prospect "*" --> "0..1" Workflow : uses
```

### Pydantic DTO and Schema Classes

```mermaid
classDiagram
    class BaseModel {
        <<Pydantic>>
    }

    class WebPage {
        +url: str
        +htmlContent: str
        +statusCode: int
        +fetchTimeMs: int
    }

    class CompanyProfile {
        +name: str
        +description: str
        +employeeCount: int
        +revenue: str
        +location: str
        +industries: list~str~
    }

    class TechStackEntry {
        +technology: str
        +category: str
        +confidence: float
        +source: str
    }

    class JobPosting {
        +title: str
        +department: str
        +url: str
        +postedDate: str
    }

    class EmailValidationResult {
        +email: str
        +isValid: bool
        +reason: str
    }

    class CompetitorMapping {
        +technology: str
        +competitors: list~str~
        +painPoints: dict~str, str~
    }

    class ICPCriteria {
        +industries: List~str~
        +min_revenue: int
        +max_revenue: int
        +min_employees: int
        +max_employees: int
        +locations: List~str~
        +tech_stack: List~str~
        +behaviors: List~str~
        +operator: str
        +check_ranges() ICPCriteria
    }

    class PersonaDefinition {
        +job_titles: List~str~
        +seniority_levels: List~str~
        +functions: List~str~
        +exclude_titles: List~str~
    }

    class ThresholdConfig {
        +min_confidence_score: float
        +max_errors_allowed: int
        +hitl_confidence_threshold: float
        +auto_approve_threshold: float
    }

    class ProspectSummary {
        +id: UUID
        +display_id: str
        +company_name: str
        +status: str
        +updated_at: datetime
    }

    class ProspectDetail {
        +id: UUID
        +display_id: str
        +company_name: str
        +website: str
        +status: str
        +state_json: dict
        +created_at: datetime
        +updated_at: datetime
        +workflow_thread_id: str
    }

    BaseModel <|-- WebPage
    BaseModel <|-- CompanyProfile
    BaseModel <|-- TechStackEntry
    BaseModel <|-- JobPosting
    BaseModel <|-- EmailValidationResult
    BaseModel <|-- CompetitorMapping
    BaseModel <|-- ICPCriteria
    BaseModel <|-- PersonaDefinition
    BaseModel <|-- ThresholdConfig
    BaseModel <|-- ProspectSummary
    BaseModel <|-- ProspectDetail
```

---

## Core Infrastructure Classes

### Circuit Breaker FSM

```mermaid
classDiagram
    class CircuitBreakerState {
        <<Enumeration>>
        CLOSED
        OPEN
        HALF_OPEN
    }

    class CircuitBreaker {
        -service_states: dict~str, CircuitBreakerState~
        -failure_counts: dict~str, int~
        -last_failure_times: dict~str, float~
        -failure_threshold: int
        -reset_timeout_sec: int
        +__init__(failure_threshold: int, reset_timeout_sec: int)
        +check_health(service_name: str) CircuitBreakerState
        +record_success(service_name: str) None
        +record_failure(service_name: str) None
    }

    class PubSub {
        -subscribers: Dict~str, Set~Queue~~
        +publish(topic: str, message: Any) None
        +subscribe(topic: str) Queue
        +unsubscribe(topic: str, queue: Queue) None
    }

    class Settings {
        <<Pydantic BaseSettings>>
        +APP_ENV: str
        +LOG_LEVEL: str
        +DATABASE_URL: str
        +LLM_PROVIDER: str
        +LLM_MODEL: str
        +LLM_API_KEY: str
        +GROQ_API_KEYS: str
        +MAX_RETRIES: int
        +HITL_TIMEOUT_SECONDS: int
        +get_async_db_url() str
        +get_sync_db_url() str
        +get_checkpoint_db_url() str
    }

    CircuitBreaker --> CircuitBreakerState : manages
```

### Exception Hierarchy

```mermaid
classDiagram
    class Exception {
        <<Built-in>>
    }

    class RateLimitError {
        <<HTTP 429>>
    }

    class TimeoutError {
        <<External Call Timeout>>
    }

    class ServiceUnavailableError {
        <<Circuit Breaker Open>>
    }

    Exception <|-- RateLimitError
    Exception <|-- TimeoutError
    Exception <|-- ServiceUnavailableError
```

---

## API Provider Framework

The API provider framework implements the **Factory Pattern** combined with the **Strategy Pattern** to enable pluggable external API integrations:

```mermaid
classDiagram
    class BaseAPIProvider {
        <<Abstract>>
        +fetch_entries(config: dict)* list~dict~
    }

    class NewsAPIProvider {
        +fetch_entries(config: dict) list~dict~
    }

    class GitHubAPIProvider {
        +fetch_entries(config: dict) list~dict~
    }

    class ApifyLinkedInProvider {
        +fetch_entries(config: dict) list~dict~
    }

    class GenericAPIProvider {
        +fetch_entries(config: dict) list~dict~
    }

    class APIProviderFactory {
        -_providers: dict~str, BaseAPIProvider~
        +__init__()
        +register_provider(source_type: str, provider: BaseAPIProvider) None
        +get_provider(source_type: str) BaseAPIProvider
    }

    BaseAPIProvider <|-- NewsAPIProvider
    BaseAPIProvider <|-- GitHubAPIProvider
    BaseAPIProvider <|-- ApifyLinkedInProvider
    BaseAPIProvider <|-- GenericAPIProvider

    APIProviderFactory o-- BaseAPIProvider : manages
    APIProviderFactory --> NewsAPIProvider : creates
    APIProviderFactory --> GitHubAPIProvider : creates
    APIProviderFactory --> ApifyLinkedInProvider : creates
    APIProviderFactory --> GenericAPIProvider : creates
```

---

## Toolbox Facade Composition

The `Toolbox` is the central **Facade** (GoF) that aggregates all external service interactions into a single, unified interface for agents:

```mermaid
classDiagram
    class Toolbox {
        -_llm_service: LLMServiceProtocol
        -_scraping_service: ScrapingServiceProtocol
        -_enrichment_service: EnrichmentServiceProtocol
        -circuit_breaker: CircuitBreaker
        -event_store: list~dict~
        +fetch_webpage(url: str, timeout: int) WebPage
        +fetch_crunchbase(company: str) CompanyProfile
        +scrape_linkedin(company: str) dict
        +detect_tech_stack(html: str, domain: str) list~TechStackEntry~
        +scrape_careers_page(url: str) list~JobPosting~
        +validate_email(email: str) EmailValidationResult
        +get_competitor_info(tech: str) CompetitorMapping
        +emit_event(type: str, payload: Any) None
        +send_webhook(url: str, payload: Any) None
        +generate_text(prompt: str, fallback: str) str
        +get_llm(strategy: str) ChatModel
        +find_company_employees(company: str) list~dict~
        +enrich_contact(name: str, domain: str) dict
        +fetch_rss_entries(url: str) list~dict~
        +fetch_jobs(company: str) list~dict~
    }

    class LLMServiceProtocol {
        <<Protocol>>
    }
    class ScrapingServiceProtocol {
        <<Protocol>>
    }
    class EnrichmentServiceProtocol {
        <<Protocol>>
    }
    class CircuitBreaker {
        +check_health(service: str) State
        +record_success(service: str) None
        +record_failure(service: str) None
    }

    Toolbox *-- LLMServiceProtocol : composition
    Toolbox *-- ScrapingServiceProtocol : composition
    Toolbox *-- EnrichmentServiceProtocol : composition
    Toolbox *-- CircuitBreaker : composition
```

---

## Complete System Class Map

The following diagram shows the full composition of the system, illustrating how every major class relates to every other:

```mermaid
classDiagram
    %% Core
    Settings --> Toolbox : configures
    CircuitBreaker --> Toolbox : protects calls
    PubSub --> WorkflowService : broadcasts events

    %% Agent Layer
    AgentRegistry --> AgentNode : stores
    SafeAgentWrapper --> AgentNode : wraps
    DynamicPlannerNode --> AgentRegistry : queries
    DynamicPlannerNode --> Toolbox : uses
    DynamicPlannerNode --> MemoryService : uses

    %% Service Layer
    Toolbox --> LLMServiceProtocol : delegates
    Toolbox --> ScrapingServiceProtocol : delegates
    Toolbox --> EnrichmentServiceProtocol : delegates
    WorkflowService --> HITLService : creates requests
    HITLService --> MemoryService : persists
    TriggerMonitor --> APIProviderFactory : fetches events
    TriggerMonitor --> WorkflowService : submits prospects
    ConfigService --> Config : reads/writes

    %% Data Layer
    MemoryService --> Prospect : CRUD
    MemoryService --> HITLRequest : CRUD
    MemoryService --> ProcessedEvent : dedup
```

---

<p align="center">
  <a href="README.md">Backend README</a> &#8226;
  <a href="SEQUENCE_FLOW.md">Sequence Flows</a> &#8226;
  <a href="SOLID_PRINCIPLES.md">SOLID</a> &#8226;
  <a href="RELIABILITY.md">Reliability</a> &#8226;
  <a href="AGENTIC_FLOW.md">Agentic Flow</a> &#8226;
  <a href="LLD_ARCHITECTURE.md">LLD</a> &#8226;
  <a href="APPLICATION_FLOW.md">App Flow</a>
</p>