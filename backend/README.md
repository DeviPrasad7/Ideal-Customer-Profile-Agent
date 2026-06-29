# 🧠 Backend Hub: The Cognitive Engine

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/LangGraph-Agentic%20Flow-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql" />
</div>

Welcome to the beating heart of ICP-X. The backend is a masterclass in modern software engineering, seamlessly blending **deterministic API layers** with **probabilistic agentic workflows**.

This is not a simple CRUD app. This is an **autonomous decision-making engine** built for scale, reliability, and precision.

---

## 📖 Deep Dive Documentation

To truly appreciate the engineering marvel of this backend, we have divided the documentation into dedicated, highly detailed sections. **Prepare to have your mind blown:**

- 🧬 **[Class Architecture & LLD](./CLASS_DIAGRAM.md)**: Explore our heavily decoupled Domain-Driven Design and comprehensive class diagrams.
- 🌊 **[End-to-End Sequence Flow](./SEQUENCE_FLOW.md)**: A deep dive into the global asynchronous pipeline with detailed sequence diagrams.
- 🧱 **[SOLID & Design Patterns](./SOLID_PRINCIPLES.md)**: How we achieve a zero-tech-debt environment using rigorous SOLID principles and GoF patterns.
- 🧠 **[Dynamic Agentic Flow](./AGENTIC_FLOW.md)**: Discover how LangGraph powers our cognitive, self-correcting agents and state machines.
- 🛡️ **[Reliability Engineering](./RELIABILITY.md)**: Our obsessive approach to fault tolerance, idempotency, and circuit breakers.

---

## 🛡️ Reliability & Fault Tolerance

We don't just hope things work; we engineer them so they can't fail.
- **Connection Pooling Excellence**: Optimized SQLAlchemy session management and PgBouncer integration ensure we never drop a database connection under load.
- **Idempotent Workflows**: Every agentic action is idempotent. If a node fails, the graph safely replays without duplicating data or side effects.
- **Graceful Degradation**: If an external enrichment API goes down, the system seamlessly falls back to cached data or alternative data providers without failing the entire prospect evaluation.

## 🛠️ Development

- **Run Locally**: `uvicorn src.api.app:app --reload`
- **Run Tests**: `pytest -v`
- **Database Migrations**: `alembic upgrade head`

---
🔙 **[Back to Main Repository](../README.md)** | 💻 **[Explore Frontend](../frontend/README.md)**
