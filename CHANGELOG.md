# Changelog

All notable changes to MemNexus will be documented in this file.

## [0.1.0] - 2026-02-20

### 🎉 Initial Release - Complete 3-Phase Development

#### Phase 1: Rapid Prototyping
- CLI Wrapper mode for wrapping existing CLI tools (claude, kimi, codex)
- Shared Memory system with LanceDB vector storage
- Context Manager for semantic search
- REST API + WebSocket support
- Basic HTML dashboard

**New Files:**
- `src/memnexus/agents/base.py` - BaseAgent abstract class
- `src/memnexus/agents/wrapper.py` - CLI Wrapper implementation
- `src/memnexus/memory/store.py` - MemoryStore with LanceDB
- `src/memnexus/memory/context.py` - ContextManager

#### Phase 2: Protocol Implementation
- ACP Protocol Server (JSON-RPC over stdio)
- Native ACP connection for Claude Code and Kimi CLI
- Full LlamaIndex RAG Pipeline with document chunking
- Real-time memory synchronization with pub/sub
- WebSocket sync endpoint

**New Files:**
- `src/memnexus/protocols/acp.py` - ACP Protocol implementation
- `src/memnexus/memory/rag.py` - RAG Pipeline with LlamaIndex
- `src/memnexus/memory/sync.py` - Memory sync system

#### Phase 3: Full Product
- Multi-Agent Orchestrator with dependency management
- Task Scheduler with critical path analysis
- Human Intervention System with approval workflows
- React Frontend with real-time dashboard

**New Files:**
- `src/memnexus/orchestrator/engine.py` - Orchestration engine
- `src/memnexus/orchestrator/scheduler.py` - Task scheduler
- `src/memnexus/orchestrator/intervention.py` - Intervention system
- `frontend/` - Complete React frontend application

### API Endpoints

#### New Endpoints
- `POST /api/v1/sessions/{id}/agents/connect` - ACP agent connection
- `POST /api/v1/sessions/{id}/rag/query` - RAG query
- `POST /api/v1/sessions/{id}/plan` - Create execution plan
- `POST /api/v1/sessions/{id}/execute` - Execute orchestration plan
- `GET /api/v1/sessions/{id}/interventions` - List interventions
- `POST /api/v1/interventions/{id}/resolve` - Resolve intervention
- `WS /ws/sync/{session_id}` - Real-time memory sync

### CLI Commands

#### New Commands
- `memnexus acp-connect` - Connect agent via ACP protocol
- `memnexus rag-ingest` - Ingest file to RAG pipeline
- `memnexus rag-query` - Query RAG pipeline
- `memnexus sync-watch` - Watch real-time memory sync
- `memnexus orchestrate` - Start multi-agent orchestration
- `memnexus plan-show` - Display execution plan
- `memnexus intervention-list` - Show pending interventions
- `memnexus intervention-resolve` - Resolve an intervention

### Statistics
- Total Lines of Code: ~11,334
- Python Files: 20+
- Frontend Files: 16
- Git Commits: 3 major milestones

[0.1.0]: https://github.com/Leeelics/MemNexus/releases/tag/v0.1.0
