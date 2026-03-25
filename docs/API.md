# MemNexus API Reference

Complete reference for the MemNexus REST API.

## Base URL

```
http://localhost:8080
```

All API endpoints are prefixed with `/api/v1` unless otherwise noted.

## Authentication

Currently, MemNexus does not require authentication. It runs locally and only accepts connections from localhost by default.

## Content Type

All requests and responses use JSON:

```
Content-Type: application/json
```

## Core Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "initialized": true,
  "project": "/path/to/project"
}
```

### Project Stats

```http
GET /stats
```

**Response:**
```json
{
  "project_path": "/home/user/my-project",
  "initialized": true,
  "has_git": true,
  "git_commits_indexed": 42,
  "code_symbols_indexed": 156,
  "total_memories": 198
}
```

## Memory Endpoints

### Search All Memories

```http
GET /api/v1/search?query={query}&limit={limit}
```

**Parameters:**
- `query` (required): Search query
- `limit` (optional): Maximum results [default: 5]

**Response:**
```json
[
  {
    "content": "def authenticate_user(username: str, password: str)...",
    "source": "code:auth.py",
    "score": 0.92,
    "metadata": {
      "symbol_name": "authenticate_user",
      "symbol_type": "function",
      "file_path": "auth.py",
      "start_line": 24
    }
  }
]
```

### Add Memory

```http
POST /api/v1/memory
```

**Request Body:**
```json
{
  "content": "Important decision about architecture",
  "source": "user",
  "metadata": {
    "category": "decision",
    "tags": ["architecture", "database"]
  }
}
```

**Response:**
```json
{
  "id": "abc123",
  "status": "added"
}
```

## Git Endpoints

### Index Git History

```http
POST /api/v1/git/index?limit={limit}
```

**Parameters:**
- `limit` (optional): Maximum commits to index [default: 1000]

**Response:**
```json
{
  "indexed": 42,
  "total": 42,
  "type": "git_commits",
  "errors": []
}
```

### Search Git History

```http
GET /api/v1/git/search?query={query}&limit={limit}
```

**Parameters:**
- `query` (required): Search query
- `limit` (optional): Maximum results [default: 5]

**Response:**
```json
[
  {
    "commit_hash": "a1b2c3d4",
    "message": "feat(auth): Add JWT authentication",
    "author": "John Doe <john@example.com>",
    "date": "2024-03-20T10:30:00",
    "files_changed": ["auth.py", "models.py"],
    "relevance_score": 0.95
  }
]
```

## Code Endpoints

### Index Codebase

```http
POST /api/v1/code/index
```

**Request Body:**
```json
{
  "languages": ["python"],
  "file_patterns": ["*.py"]
}
```

**Response:**
```json
{
  "indexed": 156,
  "files_processed": 23,
  "type": "code_symbols",
  "languages": ["python"],
  "errors": []
}
```

### Search Code

```http
GET /api/v1/code/search?query={query}&language={language}&symbol_type={type}&limit={limit}
```

**Parameters:**
- `query` (required): Search query
- `language` (optional): Filter by language (e.g., "python")
- `symbol_type` (optional): Filter by type ("function", "class", "method")
- `limit` (optional): Maximum results [default: 5]

**Response:**
```json
[
  {
    "content": "def authenticate_user(self, username: str, password: str) -> Optional[User]:",
    "source": "code:auth.py",
    "score": 0.94,
    "metadata": {
      "symbol_name": "authenticate_user",
      "symbol_type": "method",
      "file_path": "auth.py",
      "start_line": 24,
      "signature": "def authenticate_user(self, username: str, password: str) -> Optional[User]:",
      "docstring": "Authenticate a user with credentials."
    }
  }
]
```

### Find Symbol

```http
GET /api/v1/code/symbol/{name}
```

**Parameters:**
- `name` (path): Symbol name (e.g., "authenticate_user" or "AuthController.login")

**Response:**
```json
{
  "content": "def authenticate_user(self, username: str, password: str) -> Optional[User]:\n    ...",
  "source": "code:auth.py",
  "score": 1.0,
  "metadata": {
    "symbol_name": "authenticate_user",
    "symbol_type": "method",
    "file_path": "auth.py",
    "start_line": 24,
    "signature": "def authenticate_user(self, username: str, password: str) -> Optional[User]:",
    "docstring": "Authenticate a user with credentials."
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Symbol 'unknown_function' not found"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Not found
- `503` - Service unavailable (CodeMemory not initialized)

## Examples

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# Search memories
curl "http://localhost:8080/api/v1/search?query=authentication&limit=3"

# Index Git
curl -X POST "http://localhost:8080/api/v1/git/index?limit=100"

# Index code
curl -X POST http://localhost:8080/api/v1/code/index \
  -H "Content-Type: application/json" \
  -d '{"languages": ["python"]}'

# Search code
curl "http://localhost:8080/api/v1/code/search?query=login&type=function"

# Add memory
curl -X POST http://localhost:8080/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Use Redis for caching session data",
    "source": "decision",
    "metadata": {"category": "architecture"}
  }'
```

### Python Example

```python
import requests

base_url = "http://localhost:8080"

# Search
response = requests.get(f"{base_url}/api/v1/search", params={"query": "auth"})
results = response.json()

# Index code
response = requests.post(f"{base_url}/api/v1/code/index")
stats = response.json()

# Find symbol
response = requests.get(f"{base_url}/api/v1/code/symbol/authenticate_user")
symbol = response.json()
```

### JavaScript Example

```javascript
const baseUrl = 'http://localhost:8080';

// Search memories
const response = await fetch(`${baseUrl}/api/v1/search?query=authentication`);
const results = await response.json();

// Index Git
await fetch(`${baseUrl}/api/v1/git/index`, { method: 'POST' });

// Search code
const codeResponse = await fetch(
  `${baseUrl}/api/v1/code/search?query=login&type=function`
);
const codeResults = await codeResponse.json();
```

## Rate Limiting

Currently, no rate limiting is implemented. Since MemNexus runs locally, this is typically not needed.

## CORS

CORS is enabled for all origins by default. For production use, you may want to restrict this.

## WebSocket

WebSocket support is planned for future versions for real-time memory updates.
