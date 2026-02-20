"""FastAPI server for MemNexus."""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from memnexus.core.config import settings
from memnexus.core.session import SessionManager
from memnexus.memory.store import MemoryStore

# Global state
session_manager = SessionManager()
memory_store: Optional[MemoryStore] = None
connections: Dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Data directory: {settings.DATA_DIR}")
    
    # Ensure directories exist
    settings.memory_dir
    settings.sessions_dir
    settings.logs_dir
    
    # Initialize memory store
    global memory_store
    memory_store = MemoryStore()
    await memory_store.initialize()
    print("Memory store initialized")
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Agent Collaboration Orchestration System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "phase": "Phase 1 - Rapid Prototyping",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "memory_store": "connected" if memory_store else "disconnected",
    }


# Session API

@app.get("/api/v1/sessions")
async def list_sessions() -> List[dict]:
    """List all sessions."""
    sessions = await session_manager.list_all()
    return [s.to_dict() for s in sessions]


@app.post("/api/v1/sessions")
async def create_session(data: dict) -> dict:
    """Create a new session."""
    from memnexus.core.session import ExecutionStrategy
    
    session = await session_manager.create(
        name=data.get("name", "Unnamed Session"),
        description=data.get("description", ""),
        strategy=ExecutionStrategy(data.get("strategy", "sequential")),
        working_dir=data.get("working_dir", "."),
    )
    return session.to_dict()


@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str) -> Optional[dict]:
    """Get session by ID."""
    session = await session_manager.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return session.to_dict()


@app.post("/api/v1/sessions/{session_id}/start")
async def start_session(session_id: str) -> dict:
    """Start a session."""
    success = await session_manager.update_status(
        session_id,
        status="running",
    )
    if not success:
        return {"error": "Session not found"}
    return {"message": "Session started"}


@app.post("/api/v1/sessions/{session_id}/pause")
async def pause_session(session_id: str) -> dict:
    """Pause a session."""
    success = await session_manager.update_status(
        session_id,
        status="paused",
    )
    if not success:
        return {"error": "Session not found"}
    return {"message": "Session paused"}


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete session."""
    success = await session_manager.delete(session_id)
    if not success:
        return {"error": "Session not found"}
    return {"message": "Session deleted"}


# Agent API

@app.get("/api/v1/sessions/{session_id}/agents")
async def list_agents(session_id: str) -> List[dict]:
    """List agents in a session."""
    session = await session_manager.get(session_id)
    if not session:
        return []
    return [a.to_dict() for a in session.agents]


@app.post("/api/v1/sessions/{session_id}/agents")
async def add_agent(session_id: str, data: dict) -> dict:
    """Add agent to session."""
    from memnexus.core.session import AgentConfig
    
    config = AgentConfig(
        role=data.get("role", "backend"),
        cli=data.get("cli", "claude"),
        protocol=data.get("protocol", "acp"),
        working_dir=data.get("working_dir", "."),
    )
    
    agent = await session_manager.add_agent(session_id, config)
    if not agent:
        return {"error": "Session not found"}
    return agent.to_dict()


@app.post("/api/v1/sessions/{session_id}/agents/launch")
async def launch_agent(session_id: str, data: dict) -> dict:
    """Launch an agent in wrapper mode."""
    result = await session_manager.launch_agent(
        session_id=session_id,
        cli=data.get("cli"),
        name=data.get("name"),
        working_dir=data.get("working_dir"),
    )
    
    if result is None:
        return {"error": "Session not found"}
    
    return result


# Memory API

@app.get("/api/v1/sessions/{session_id}/memory")
async def get_session_memory(
    session_id: str,
    query: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """Get or search session memory."""
    if query:
        # Search mode
        results = await session_manager.search_context(session_id, query, limit)
        if results is None:
            return {"error": "Session not found"}
        return {"query": query, "results": results}
    else:
        # List mode
        context = session_manager.get_context_manager(session_id)
        if not context:
            return {"error": "Session not found"}
        
        memories = await context.get_conversation_history(limit=limit)
        return {
            "session_id": session_id,
            "memories": [m.to_dict() for m in memories],
        }


@app.post("/api/v1/sessions/{session_id}/memory")
async def add_memory(session_id: str, data: dict) -> dict:
    """Add a memory entry to session."""
    context = session_manager.get_context_manager(session_id)
    if not context:
        return {"error": "Session not found"}
    
    entry_id = await context.store_agent_output(
        agent=data.get("source", "user"),
        content=data.get("content"),
        memory_type=data.get("type", "generic"),
        metadata=data.get("metadata", {}),
    )
    
    return {"id": entry_id, "message": "Memory added"}


@app.get("/api/v1/memory/stats")
async def memory_stats() -> dict:
    """Get memory store statistics."""
    if memory_store is None:
        return {"error": "Memory store not initialized"}
    
    stats = await memory_store.get_stats()
    return stats


# Phase 3: Orchestration API

@app.post("/api/v1/sessions/{session_id}/plan")
async def create_execution_plan(
    session_id: str,
    data: dict,
) -> dict:
    """Create an execution plan for a session."""
    from memnexus.orchestrator.engine import OrchestratorEngine, OrchestrationTask
    from memnexus.core.session import ExecutionStrategy, AgentRole
    
    orchestrator = OrchestratorEngine(session_manager)
    await orchestrator.initialize(session_id)
    
    strategy = ExecutionStrategy(data.get("strategy", "sequential"))
    
    # Convert task data to OrchestrationTask objects
    tasks = []
    for task_data in data.get("tasks", []):
        task = OrchestrationTask(
            id=task_data.get("id", f"task_{len(tasks)}"),
            name=task_data.get("name", "Unnamed Task"),
            description=task_data.get("description", ""),
            role=AgentRole(task_data.get("role", "backend")),
            prompt=task_data.get("prompt", ""),
            dependencies=task_data.get("dependencies", []),
        )
        tasks.append(task)
    
    plan = await orchestrator.create_plan(session_id, strategy, tasks)
    
    return {
        "session_id": plan.session_id,
        "strategy": plan.strategy.value,
        "tasks": [t.to_dict() for t in plan.tasks],
        "phases": plan.phases,
        "progress": plan.calculate_progress(),
    }


@app.post("/api/v1/sessions/{session_id}/execute")
async def execute_plan(
    session_id: str,
    data: dict,
) -> dict:
    """Execute the current plan for a session."""
    from memnexus.orchestrator.engine import OrchestratorEngine
    
    orchestrator = OrchestratorEngine(session_manager)
    await orchestrator.initialize(session_id)
    
    # Get existing plan or create new one
    plan = orchestrator._plans.get(session_id)
    if not plan:
        return {"error": "No plan found. Create a plan first."}
    
    # Execute in background
    async def execute():
        success = await orchestrator.execute_plan(plan)
        return success
    
    # Start execution
    asyncio.create_task(execute())
    
    return {
        "status": "started",
        "session_id": session_id,
        "task_count": len(plan.tasks),
    }


@app.get("/api/v1/sessions/{session_id}/progress")
async def get_execution_progress(session_id: str) -> dict:
    """Get execution progress for a session."""
    from memnexus.orchestrator.engine import OrchestratorEngine
    
    orchestrator = OrchestratorEngine(session_manager)
    plan = orchestrator._plans.get(session_id)
    
    if not plan:
        return {"error": "No plan found"}
    
    return {
        "session_id": session_id,
        "progress": plan.calculate_progress(),
        "tasks": [t.to_dict() for t in plan.tasks],
        "phases": plan.phases,
    }


@app.post("/api/v1/sessions/{session_id}/cancel")
async def cancel_execution(session_id: str) -> dict:
    """Cancel execution for a session."""
    from memnexus.orchestrator.engine import OrchestratorEngine
    
    orchestrator = OrchestratorEngine(session_manager)
    await orchestrator.cancel(session_id)
    
    return {"status": "cancelled", "session_id": session_id}


# Phase 3: Intervention API

@app.get("/api/v1/sessions/{session_id}/interventions")
async def get_interventions(
    session_id: str,
    status: Optional[str] = None,
) -> List[dict]:
    """Get interventions for a session."""
    from memnexus.orchestrator.intervention import HumanInterventionSystem, InterventionStatus
    
    intervention_system = HumanInterventionSystem()
    await intervention_system.initialize()
    
    if status:
        interventions = intervention_system.get_session_interventions(
            session_id, InterventionStatus(status)
        )
    else:
        interventions = intervention_system.get_session_interventions(session_id)
    
    return [i.to_dict() for i in interventions]


@app.post("/api/v1/interventions/{intervention_id}/resolve")
async def resolve_intervention(
    intervention_id: str,
    data: dict,
) -> dict:
    """Resolve an intervention."""
    from memnexus.orchestrator.intervention import HumanInterventionSystem
    
    intervention_system = HumanInterventionSystem()
    await intervention_system.initialize()
    
    resolution = data.get("resolution", {})
    resolved_by = data.get("resolved_by", "human")
    
    point = await intervention_system.resolve(
        intervention_id, resolution, resolved_by
    )
    
    if point:
        return point.to_dict()
    return {"error": "Intervention not found"}


# Phase 2: ACP Protocol API

@app.post("/api/v1/sessions/{session_id}/agents/connect")
async def connect_agent_acp(
    session_id: str,
    data: dict,
) -> dict:
    """Connect an agent via ACP protocol."""
    from memnexus.protocols.acp import ACPProtocolServer
    
    cli = data.get("cli", "claude")
    name = data.get("name", cli)
    working_dir = data.get("working_dir", ".")
    
    # Create protocol server
    acp_server = ACPProtocolServer(session_manager)
    await acp_server.start()
    
    try:
        conn = await acp_server.connect_agent(
            cli=cli,
            session_id=session_id,
            working_dir=working_dir,
        )
        
        if conn:
            return {
                "status": "connected",
                "connection_id": id(conn),
                "agent": name,
                "protocol": "acp",
            }
        else:
            return {"error": "Failed to connect agent"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/sessions/{session_id}/agents/{agent_id}/prompt")
async def send_prompt(
    session_id: str,
    agent_id: str,
    data: dict,
) -> dict:
    """Send a prompt to an ACP-connected agent."""
    prompt = data.get("prompt", "")
    
    # Get session and find ACP connection
    session = await session_manager.get(session_id)
    if not session:
        return {"error": "Session not found"}
    
    # TODO: Implement prompt sending via stored ACP connection
    return {
        "status": "sent",
        "prompt": prompt,
        "agent_id": agent_id,
    }


# Phase 2: RAG API

@app.post("/api/v1/sessions/{session_id}/rag/ingest")
async def rag_ingest(
    session_id: str,
    data: dict,
) -> dict:
    """Ingest a document into RAG pipeline."""
    from memnexus.memory.rag import RAGPipeline, Document
    
    content = data.get("content", "")
    source = data.get("source", "unknown")
    doc_type = data.get("type", "text")
    
    pipeline = RAGPipeline(session_id=session_id)
    await pipeline.initialize()
    
    doc = Document(
        content=content,
        source=source,
        doc_type=doc_type,
    )
    
    chunk_ids = await pipeline.ingest_document(doc)
    
    return {
        "document_id": doc.doc_id,
        "chunks": len(chunk_ids),
        "chunk_ids": chunk_ids,
    }


@app.post("/api/v1/sessions/{session_id}/rag/query")
async def rag_query(
    session_id: str,
    data: dict,
) -> dict:
    """Query the RAG pipeline."""
    from memnexus.memory.rag import RAGPipeline
    
    query_text = data.get("query", "")
    top_k = data.get("top_k", 5)
    
    pipeline = RAGPipeline(session_id=session_id)
    await pipeline.initialize()
    
    results = await pipeline.query_with_context(query_text, top_k)
    
    return results


@app.post("/api/v1/sessions/{session_id}/rag/ingest-file")
async def rag_ingest_file(
    session_id: str,
    data: dict,
) -> dict:
    """Ingest a file into RAG pipeline."""
    from memnexus.memory.rag import RAGPipeline
    
    file_path = data.get("file_path", "")
    
    if not file_path:
        return {"error": "file_path required"}
    
    pipeline = RAGPipeline(session_id=session_id)
    await pipeline.initialize()
    
    try:
        chunk_ids = await pipeline.ingest_file(file_path)
        return {
            "file_path": file_path,
            "chunks": len(chunk_ids),
            "chunk_ids": chunk_ids,
        }
    except Exception as e:
        return {"error": str(e)}


# Phase 2: Real-time Sync API

@app.websocket("/ws/sync/{session_id}")
async def sync_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for real-time memory sync."""
    await websocket.accept()
    
    from memnexus.memory.sync import MemorySyncManager
    
    # Create sync manager
    sync_manager = MemorySyncManager(session_id=session_id)
    await sync_manager.initialize()
    
    # Watch for events
    event_queue = await sync_manager.watch()
    
    try:
        await websocket.send_json({
            "type": "sync_connected",
            "session_id": session_id,
        })
        
        while True:
            # Check for events
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                await websocket.send_json(event.to_dict())
            except asyncio.TimeoutError:
                pass
            
            # Check for client messages
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.1
                )
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                pass
                
    except WebSocketDisconnect:
        await sync_manager.close()
    except Exception as e:
        print(f"Sync WebSocket error: {e}")
        await sync_manager.close()


# WebSocket for real-time updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    client_id = str(id(websocket))
    connections[client_id] = websocket
    
    try:
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
        })
        
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle different message types
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                session_id = data.get("session_id")
                await websocket.send_json({
                    "type": "subscribed",
                    "session_id": session_id,
                })
                
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })
                
    except WebSocketDisconnect:
        del connections[client_id]
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if client_id in connections:
            del connections[client_id]


# Simple HTML dashboard

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple HTML dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MemNexus Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            h1 {
                color: #333;
            }
            .status {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border-radius: 4px;
                display: inline-block;
            }
            .status.phase1 {
                background: #2196F3;
            }
            .section {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .log {
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
                height: 400px;
                overflow-y: auto;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }
            .log-entry {
                padding: 4px 0;
                border-bottom: 1px solid #333;
            }
            .timestamp {
                color: #666;
                font-size: 12px;
            }
            .agent-claude { color: #4CAF50; }
            .agent-kimi { color: #2196F3; }
            .agent-codex { color: #FF9800; }
            .badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin-left: 8px;
            }
            .badge.new {
                background: #4CAF50;
                color: white;
            }
            .feature-list {
                list-style: none;
                padding: 0;
            }
            .feature-list li {
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .feature-list li:before {
                content: "✓ ";
                color: #4CAF50;
                font-weight: bold;
            }
            .feature-list li.pending:before {
                content: "○ ";
                color: #999;
            }
        </style>
    </head>
    <body>
        <h1>🧠 MemNexus Dashboard</h1>
        <div class="status phase1">● Phase 1 - Rapid Prototyping</div>
        
        <div class="section">
            <h2>Phase 1 Features <span class="badge new">NEW</span></h2>
            <ul class="feature-list">
                <li>CLI Wrapper Mode - Wrap existing CLI tools (claude, kimi, codex)</li>
                <li>Shared Memory - LanceDB vector storage for agent context</li>
                <li>Context Manager - Semantic search and retrieval</li>
                <li>Session-based Memory - Isolated context per session</li>
                <li class="pending">ACP Protocol Server (Phase 2)</li>
                <li class="pending">React Frontend (Phase 3)</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Quick Actions</h2>
            <button onclick="createSession()">Create Session</button>
            <button onclick="listSessions()">List Sessions</button>
            <button onclick="memoryStats()">Memory Stats</button>
        </div>
        
        <h2>Real-time Logs</h2>
        <div class="log" id="log">
            <div class="log-entry">
                <span class="timestamp">[System]</span>
                MemNexus Dashboard connected
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const log = document.getElementById('log');
            
            function addLog(message, type = 'info') {
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                const time = new Date().toLocaleTimeString();
                entry.innerHTML = `<span class="timestamp">[${time}]</span> ${message}`;
                log.appendChild(entry);
                log.scrollTop = log.scrollHeight;
            }
            
            async function createSession() {
                const response = await fetch('/api/v1/sessions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: 'New Session', strategy: 'sequential'})
                });
                const data = await response.json();
                addLog(`Created session: ${data.id}`, 'success');
            }
            
            async function listSessions() {
                const response = await fetch('/api/v1/sessions');
                const data = await response.json();
                addLog(`Found ${data.length} sessions`, 'info');
            }
            
            async function memoryStats() {
                const response = await fetch('/api/v1/memory/stats');
                const data = await response.json();
                addLog(`Memory: ${JSON.stringify(data)}`, 'info');
            }
            
            ws.onopen = () => {
                console.log('Connected to MemNexus');
                addLog('WebSocket connected', 'success');
                ws.send(JSON.stringify({type: 'subscribe', session_id: 'all'}));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data);
                
                if (data.type === 'connected') {
                    addLog(`Client ID: ${data.client_id}`, 'info');
                }
            };
            
            ws.onclose = () => {
                console.log('Disconnected');
                addLog('WebSocket disconnected', 'warning');
            };
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
