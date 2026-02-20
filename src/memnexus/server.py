"""FastAPI server for MemNexus."""

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
