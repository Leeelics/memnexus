# MemNexus API Reference

Complete reference for the MemNexus REST API and WebSocket endpoints.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

Currently, MemNexus does not require authentication. For production deployments, consider adding API key authentication.

## Sessions

### List Sessions

```http
GET /sessions
```

**Response:**
```json
[
  {
    "id": "sess_abc123",
    "name": "My Project",
    "status": "running",
    "strategy": "parallel",
    "agent_count": 3,
    "task_count": 5,
    "created_at": "2026-02-20T10:00:00Z"
  }
]
```

### Create Session

```http
POST /sessions
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "strategy": "parallel",
  "working_dir": "/path/to/project"
}
```

**Response:**
```json
{
  "id": "sess_def456",
  "name": "New Project",
  "status": "created",
  "strategy": "parallel",
  "agent_count": 0,
  "task_count": 0,
  "created_at": "2026-02-20T11:00:00Z"
}
```

### Get Session

```http
GET /sessions/{id}
```

### Start Session

```http
POST /sessions/{id}/start
```

### Pause Session

```http
POST /sessions/{id}/pause
```

### Delete Session

```http
DELETE /sessions/{id}
```

## Agents

### List Agents

```http
GET /sessions/{session_id}/agents
```

**Response:**
```json
[
  {
    "id": "ag_001",
    "session_id": "sess_abc123",
    "role": "backend",
    "cli": "claude",
    "status": "idle"
  }
]
```

### Add Agent

```http
POST /sessions/{session_id}/agents
Content-Type: application/json

{
  "role": "backend",
  "cli": "claude",
  "protocol": "acp",
  "working_dir": "."
}
```

### Launch Agent (Wrapper Mode)

```http
POST /sessions/{session_id}/agents/launch
Content-Type: application/json

{
  "cli": "claude",
  "name": "claude-backend",
  "working_dir": "/path/to/project"
}
```

### Connect Agent (ACP Protocol)

```http
POST /sessions/{session_id}/agents/connect
Content-Type: application/json

{
  "cli": "claude",
  "name": "claude-architect",
  "working_dir": "."
}
```

**Response:**
```json
{
  "status": "connected",
  "connection_id": "conn_123",
  "agent": "claude-architect",
  "protocol": "acp"
}
```

### Send Prompt to Agent

```http
POST /sessions/{session_id}/agents/{agent_id}/prompt
Content-Type: application/json

{
  "prompt": "Design a REST API for user authentication"
}
```

## Memory

### Search Memory

```http
GET /sessions/{session_id}/memory?query=API&limit=10
```

**Response:**
```json
{
  "query": "API",
  "results": [
    {
      "id": "mem_001",
      "content": "Created API endpoints for user authentication",
      "source": "claude",
      "type": "code",
      "timestamp": "2026-02-20T10:30:00Z"
    }
  ]
}
```

### Add Memory

```http
POST /sessions/{session_id}/memory
Content-Type: application/json

{
  "content": "User authentication system implemented",
  "source": "claude",
  "type": "task_result",
  "metadata": {
    "task": "auth_implementation"
  }
}
```

### Get Memory Stats

```http
GET /memory/stats
```

**Response:**
```json
{
  "total_entries": 150,
  "sessions": 5,
  "memory_types": {
    "code": 80,
    "conversation": 50,
    "file_change": 20
  }
}
```

## RAG (Retrieval Augmented Generation)

### Ingest Document

```http
POST /sessions/{session_id}/rag/ingest
Content-Type: application/json

{
  "content": "# API Documentation\n\n## Endpoints...",
  "source": "api_docs.md",
  "type": "markdown"
}
```

**Response:**
```json
{
  "document_id": "doc_abc123",
  "chunks": 5,
  "chunk_ids": ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
}
```

### Ingest File

```http
POST /sessions/{session_id}/rag/ingest-file
Content-Type: application/json

{
  "file_path": "/path/to/file.md"
}
```

### Query RAG

```http
POST /sessions/{session_id}/rag/query
Content-Type: application/json

{
  "query": "What is the authentication flow?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What is the authentication flow?",
  "results": [
    {
      "text": "The authentication flow involves...",
      "score": 0.95,
      "source": "auth_docs.md",
      "type": "markdown"
    }
  ],
  "context": "[1] Source: auth_docs.md\nContent: The authentication flow...",
  "sources": ["auth_docs.md", "readme.md"]
}
```

## Orchestration

### Create Execution Plan

```http
POST /sessions/{session_id}/plan
Content-Type: application/json

{
  "strategy": "parallel",
  "tasks": [
    {
      "id": "task_1",
      "name": "Design Architecture",
      "role": "architect",
      "prompt": "Design the system architecture",
      "dependencies": []
    },
    {
      "id": "task_2",
      "name": "Implement Backend",
      "role": "backend",
      "prompt": "Implement the API",
      "dependencies": ["task_1"]
    }
  ]
}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "strategy": "parallel",
  "tasks": [
    {
      "id": "task_1",
      "name": "Design Architecture",
      "role": "architect",
      "state": "ready"
    }
  ],
  "phases": [["task_1"], ["task_2", "task_3"]],
  "progress": 0.0
}
```

### Execute Plan

```http
POST /sessions/{session_id}/execute
Content-Type: application/json

{
  "async": true
}
```

**Response:**
```json
{
  "status": "started",
  "session_id": "sess_abc123",
  "task_count": 4
}
```

### Get Progress

```http
GET /sessions/{session_id}/progress
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "progress": 0.5,
  "tasks": [
    {
      "id": "task_1",
      "name": "Design Architecture",
      "state": "completed",
      "assigned_agent": "ag_001"
    }
  ],
  "phases": [["task_1"], ["task_2", "task_3"], ["task_4"]]
}
```

### Cancel Execution

```http
POST /sessions/{session_id}/cancel
```

## Interventions

### List Interventions

```http
GET /sessions/{session_id}/interventions?status=waiting_for_human
```

**Response:**
```json
[
  {
    "id": "int_001",
    "type": "approval",
    "title": "Review Database Schema",
    "description": "Agent has proposed schema changes",
    "session_id": "sess_abc123",
    "task_id": "task_456",
    "status": "waiting_for_human",
    "created_at": "2026-02-20T10:30:00Z",
    "deadline": "2026-02-20T11:30:00Z"
  }
]
```

### Resolve Intervention

```http
POST /interventions/{intervention_id}/resolve
Content-Type: application/json

{
  "resolution": {
    "action": "approve",
    "message": "Looks good, proceed with implementation"
  },
  "resolved_by": "human"
}
```

**Response:**
```json
{
  "id": "int_001",
  "type": "approval",
  "status": "approved",
  "resolved_at": "2026-02-20T10:35:00Z",
  "resolved_by": "human",
  "resolution": {
    "action": "approve",
    "message": "Looks good, proceed with implementation"
  }
}
```

## WebSocket

### Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    session_id: 'sess_abc123'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Message Types:**
- `connected` - Connection established
- `subscribed` - Subscription confirmed
- `task_progress` - Task execution progress
- `memory_sync` - Memory synchronization event
- `intervention_created` - New intervention
- `pong` - Heartbeat response

### Memory Sync Stream

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/sync/sess_abc123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle memory sync events
};
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": 400,
  "details": "Additional error details"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider adding rate limiting middleware.

## Pagination

List endpoints support pagination via `page` and `page_size` query parameters:

```http
GET /sessions?page=1&page_size=20
```

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"

# Create session
response = requests.post(f"{BASE_URL}/sessions", json={
    "name": "My Project",
    "strategy": "parallel"
})
session = response.json()

# Connect agent
requests.post(f"{BASE_URL}/sessions/{session['id']}/agents/connect", json={
    "cli": "claude",
    "name": "claude-architect"
})
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8080/api/v1';

// Create session
const response = await fetch(`${BASE_URL}/sessions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Project',
    strategy: 'parallel'
  })
});
const session = await response.json();
```
