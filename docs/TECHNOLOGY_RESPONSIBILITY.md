# Ignite Technology Responsibility Matrix

**Project**: Ignite (PS20)  
**Document**: `docs/TECHNOLOGY_RESPONSIBILITY.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN RESPONSIBILITY MATRIX  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary
This document establishes strict architectural boundaries for every software technology stack component in Project Ignite. It enforces segregation of concerns to prevent anti-patterns such as using LLMs for math or ML models for resource optimization.

---

## 2. Technology Responsibility Matrix

| Technology Component | Core Architectural Responsibility | Input | Output | Strict Prohibitions (**Must NOT Do**) |
| :--- | :--- | :--- | :--- | :--- |
| **LLM / Generative AI** | Unstructured report parsing, entity extraction, and natural language executive summaries. | Raw text reports, SMS messages, incident transcripts. | Structured JSON (`StructuredReport`), text narratives. | ❌ **Must NOT calculate numerical resource quantities.**<br>❌ **Must NOT make probabilistic predictions.** |
| **ML Engine (XGBoost / LightGBM)** | Probabilistic classification & regression of impact severity, risk trajectory, and population exposure. | Structured feature tensors (`SituationIntelligence`). | `SeverityAssessment` (0-5 score), `RiskAssessment` (\(\Delta S_{t+h}\)). | ❌ **Must NOT solve constraint optimization.**<br>❌ **Must NOT bypass temporal lag guardrails.** |
| **Deterministic Rules Engine** | Execution of exact mathematical calculations based on Sphere Standards. | Validated population & severity outputs from ML. | Itemized supply requirements (`ResourceRequirement`). | ❌ **Must NOT make probabilistic predictions.**<br>❌ **Must NOT ingest unvalidated raw text.** |
| **OR-Tools (Optimization)** | Constrained logistics optimization (MILP / VRP) for warehouse dispatch and fleet routing. | `ResourceRequirement`, `InventoryState`, road distance matrix. | Solved allocation plans (`AllocationPlan`). | ❌ **Must NOT parse natural language.**<br>❌ **Must NOT predict disaster severity.** |
| **LangGraph / Workflow Orchestrator** | Stateful pipeline orchestration, human-in-the-loop approvals, and agent workflow state transitions. | Shared state dictionary, step execution triggers. | State transition events, step execution status. | ❌ **Must NOT replace ML feature calculation.**<br>❌ **Must NOT bypass schema validation.** |
| **FastAPI Backend** | REST API gateway, authentication, request validation, service routing, and database transaction management. | HTTP Requests, JWT tokens, Webhook payloads. | Standardized HTTP Responses (JSON), OpenAPI specs. | ❌ **Must NOT execute ML model training.**<br>❌ **Must NOT embed heavy mathematical solvers.** |
| **PostgreSQL / PostGIS Database** | Persistent relational and spatial storage of verified incidents, feature store snapshots, and audit trails. | SQL insert queries, GeoJSON spatial layers. | Persisted database records, spatial query results. | ❌ **Must NOT execute business logic or ML.**<br>❌ **Must NOT mutate historical audit logs.** |
