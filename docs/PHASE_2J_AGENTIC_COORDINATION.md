# Phase 2J: Agentic Coordination / LangGraph

**Objective:**
Introduce the orchestrating Agent layer into the disaster relief pipeline using LangGraph and the Gemini API. The orchestrator routes reports through the deterministic data pipelines (Phases 2D-2I) and uses LLMs purely for natural language comprehension and human-readable summarization.

## 1. Architecture & State Management
**Why LangGraph?**
LangGraph enables explicit, cyclical, and check-pointed workflows. Rather than giving a single LLM autonomous control over all actions (which is mathematically unsafe for disaster logistics), LangGraph guarantees that the pipeline executes our proven deterministic engines sequentially and handles dynamic routing (like sending unverified claims to a human).

**The Shared State (`ml/src/agents/state.py`)**
The `AgentState` acts as the single source of truth across the workflow. It is fully typed and sequentially populated by the nodes, ensuring all components have access to identical validated inputs. The state includes the crucial `human_approval_state` allowing checkpoints.

## 2. Gemini Integration (`ml/src/agents/gemini_client.py`)
**Why Gemini?**
Gemini 2.5 is utilized for two specific unstructured tasks:
1. **Report Intelligence**: Extracting structured entities (hazards, locations, quantitative claims) from messy text reports using strict JSON schema output.
2. **Coordination Explanation**: Converting the numeric optimization output from Phase 2I into natural language briefs for human dispatchers.

**Limitations & Security:**
- **No Mathematical Autonomy**: Gemini NEVER calculates Severity, Trajectory, Needs, Priority, or Allocation.
- **Prompt Injection Defense**: All inputs are treated as untrusted strings. The `PROMPT_INJECTION_DETECTED` mock fallback specifically proves the graph handles extraction contamination by routing it to rejection.
- **API Key Security**: `GEMINI_API_KEY` is loaded dynamically from `os.environ`. Offline tests use the `MockGeminiClient` adapter to ensure the build pipeline runs without credentials.

## 3. Graph Nodes (`ml/src/agents/graph.py`)
1. **`report_intelligence_node`**: Extracts JSON facts.
2. **`incident_detection_node`**: Phase 2D (Normalization & Merging).
3. **`verification_node`**: Phase 2E (Trust validation).
4. **`situation_assessment_node`**: Sequentially integrates Severity (2C), Trajectory (2F), Needs (2G), and Priority (2H).
5. **`optimization_node`**: Phase 2I (Resource Allocation via OR-Tools).
6. **`coordination_node`**: Gemini drafts the action plan.
7. **`human_review_node`**: A deliberate interrupt in the graph (via `MemorySaver` checkpointer) that pauses execution until a human explicitly updates the `human_approval_state`.

## 4. Reassessment & Dynamic Reallocation
Because the graph state tracks historic inputs and limits operations to modular nodes, it naturally supports cyclical execution. If a new report arrives for `v_inc_001`, the system can resume the graph, passing through the identical deterministic pathways, resulting in an updated OR-Tools optimization.

## 5. Handoff
Phase 2J successfully merges the intelligence engines into a unified operational workflow. The backend intelligence is 100% complete.
The system is now ready for **Backend + Persistence Integration**, where this graph will be served via FastAPI and stored durably in PostgreSQL/Supabase.
