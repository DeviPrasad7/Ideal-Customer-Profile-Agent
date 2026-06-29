# 🧱 SOLID Principles & Design Patterns

<div align="center">
  <img src="https://img.shields.io/badge/Engineering-Immaculate-success?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Principles-SOLID-orange?style=for-the-badge" />
</div>

In ICP-X, we do not compromise on code quality. The backend codebase is an exhibition of pristine Software Engineering, heavily grounded in **SOLID principles** and industry-standard **Design Patterns**.

---

## 📐 Strict SOLID Adherence

Our codebase is meticulously curated to follow all five SOLID principles. This is not just theory; this is how we achieve a zero-tech-debt environment.

### 1. Single Responsibility Principle (SRP)
Every class and module has exactly one reason to change. 
- The `PostgresStorage` class *only* knows how to execute SQL queries. It knows nothing about LangGraph or HTTP.
- The `ScoringAgent` *only* evaluates a profile against a rubric. It does not fetch data, and it does not write to the database.

### 2. Open/Closed Principle (OCP)
The system is open for extension but closed for modification.
- Need a new type of scraper? You simply create a new class implementing the `IScraper` interface and register it. The core `EnrichmentAgent` logic remains **100% untouched**.

### 3. Liskov Substitution Principle (LSP)
Subtypes must be substitutable for their base types.
- Any agent inheriting from `BaseAgent` can be plugged into the LangGraph orchestrator. The orchestrator invokes `invoke(state)`, confident that the derived class will respect the contract without throwing unexpected runtime errors.

### 4. Interface Segregation Principle (ISP)
We avoid monolithic, "fat" interfaces.
- Instead of an `IDatabase` interface containing `read()`, `write()`, `migrate()`, and `backup()`, we segregate into `IProfileReader` and `IProfileWriter`. Agents only receive the specific interfaces they require.

### 5. Dependency Inversion Principle (DIP)
High-level policy modules do not depend on low-level detail modules. Both depend on abstractions.
- The business logic never imports `psycopg2` or `SQLAlchemy`. It imports the `IStorage` interface. The actual database implementation is injected at runtime via our dependency injection container.

---

## 🎨 Implemented Design Patterns

We leverage GoF (Gang of Four) patterns to elegantly solve complex orchestration challenges.

### Strategy Pattern
Used heavily in our LLM interaction layer. We have an `ILLMStrategy` interface with implementations like `CostOptimizedStrategy` (GPT-3.5) and `DeepReasoningStrategy` (GPT-4). The `ScoringAgent` dynamically selects the strategy based on the client's tier, allowing us to swap logic at runtime.

### Abstract Factory Pattern
Different clients have wildly different definitions of an "Ideal Customer Profile". We use an Abstract Factory to construct the specific validation rubrics and scoring mechanisms tailored to a specific tenant upon initialization.

### State Pattern
This is the essence of our LangGraph integration. The application behaves differently based on its current `AgentState`. The state dictates valid transitions (e.g., from `PENDING` to `ENRICHING`, but never from `PENDING` straight to `REJECTED`).

---
🔙 **[Back to Backend Hub](./README.md)**
