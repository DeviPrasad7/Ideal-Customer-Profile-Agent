<div align="center">
  <img src="https://img.shields.io/badge/Status-Ultra%20Reliable-success?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Architecture-Agentic%20Flow-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Backend-FastAPI%20%2B%20LangGraph-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge" />

  <h1>🚀 ICP-X: The Next-Gen Autonomous B2B Prospecting Engine</h1>
  <p><b>Enterprise-grade, AI-driven Ideal Customer Profile (ICP) Discovery and Routing Platform.</b></p>
</div>

---

## 🌟 Overview

Welcome to **ICP-X**, a state-of-the-art autonomous agent platform designed to revolutionize B2B SaaS prospecting. Built on an extremely robust and fault-tolerant architecture, this system autonomously discovers, qualifies, enriches, and routes Ideal Customer Profiles (ICPs) with unparalleled precision.

We have engineered this platform from the ground up to ensure **five-nines (99.999%) reliability**, employing cutting-edge Low-Level Design (LLD) patterns, advanced agentic orchestration via LangGraph, and a blazingly fast FastAPI backend.

### 🔥 Why ICP-X?
- **Cognitive Autonomous Agents**: Powered by dynamic graph-based planners that reason, adapt, and self-correct during the enrichment process.
- **Enterprise-Grade Reliability**: Implements advanced circuit breakers, automated retries, and comprehensive deadlock prevention mechanisms.
- **Immaculate LLD Engineering**: Adheres strictly to SOLID principles, leveraging abstract factory patterns, dependency injection, and state-of-the-art domain-driven design (DDD).
- **Beautiful & Reactive UI**: A pristine, highly responsive frontend built with React and Vite, offering real-time visualization of agent graphs using `@xyflow/react`.

---

## 📚 Documentation Hub

We believe world-class engineering deserves world-class documentation. Dive deep into the specific subsystems below:

- 💻 **[Frontend Documentation](./frontend/README.md)**: Explore our modern, responsive React UI, component architecture, and state management.
- ⚙️ **[Backend Engineering Hub](./backend/README.md)**: Discover the powerhouse driving the agents.
  - 🧬 **[Class Architecture & LLD](./backend/CLASS_DIAGRAM.md)**: Domain-driven design and strict typing.
  - 🌊 **[Sequence Flow](./backend/SEQUENCE_FLOW.md)**: End-to-end application lifecycle mapping.
  - 🧱 **[SOLID & Patterns](./backend/SOLID_PRINCIPLES.md)**: Immaculate software engineering practices.
  - 🧠 **[Dynamic Agentic Flow](./backend/AGENTIC_FLOW.md)**: Deep dive into LangGraph orchestration.
  - 🛡️ **[Reliability Engineering](./backend/RELIABILITY.md)**: Circuit breakers, connection pooling, and fault tolerance.

---

## 🏗️ High-Level Architecture

The system operates on a highly concurrent, state-machine-driven architecture. 

```mermaid
graph TD
    A[React/Vite Client] -->|REST / WebSockets| B(High-Performance FastAPI Layer)
    B -->|Async Dispatch| C{LangGraph Cognitive Engine}
    C -->|Discover| D[Web Scraper & Enricher Swarm]
    D --> C
    C -->|Analyze| E[AI Scoring & ML Profiling]
    E --> C
    C -->|Verify| F[Tech Stack Deterministic Scanner]
    F --> C
    C -->|Uncertainty > Threshold| G[Human-In-The-Loop (HITL)]
    G -.->|Approval Required| A
    A -.->|Callback| G
    G --> C
    C -->|Finalize| H[Downstream Webhooks & Integrations]
    
    B <--> I[(Distributed PostgreSQL / Connection Pooler)]
    C <--> I
    
    style A fill:#2b3137,stroke:#61DAFB,stroke-width:2px,color:#fff
    style B fill:#059669,stroke:#34d399,stroke-width:2px,color:#fff
    style C fill:#6366f1,stroke:#a5b4fc,stroke-width:2px,color:#fff
    style I fill:#2563eb,stroke:#93c5fd,stroke-width:2px,color:#fff
```

---

## 🚀 Getting Started

### Local Setup (Docker Compose)
Experience the power of ICP-X locally with zero friction:

1. **Environment Setup**: `cp backend/.env.example backend/.env` and insert your API keys.
2. **Ignition**: `docker-compose up --build`
3. **Explore**:
   - Frontend: `http://localhost:5173`
   - Backend OpenAPI Docs: `http://localhost:8000/docs`

### Production Deployment
Engineered for planetary scale, our Terraform scripts seamlessly provision infrastructure on GCP, utilizing Cloud Run, Cloud SQL, and advanced load balancing.

```bash
# Provision the infrastructure
cd deploy/terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT"
```

---
<div align="center">
  <i>Engineered with precision. Built for scale. Driven by AI.</i>
</div>
