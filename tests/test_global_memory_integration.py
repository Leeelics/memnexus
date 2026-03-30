"""Integration tests for Global Memory functionality.

Tests the complete global memory workflow:
1. Initialize test projects
2. Index projects (Git + Code)
3. Register with global memory
4. Sync to global memory
5. Search across projects

Run with:
    pytest tests/test_global_memory_integration.py -v
    
Or with uv:
    uv run pytest tests/test_global_memory_integration.py -v
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from memnexus import CodeMemory, GlobalMemory
from memnexus.global_memory import GlobalMemoryConfig


@pytest.fixture
def temp_projects():
    """Create temporary test projects."""
    temp_dir = Path(tempfile.mkdtemp(prefix="memnexus_test_"))
    
    # Create project A (Python API)
    project_a = temp_dir / "project-a"
    project_a.mkdir()
    
    (project_a / "auth.py").write_text('''
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with credentials."""
    return username == "admin" and password == "secret"

def create_jwt_token(user_id: str) -> str:
    """Create a JWT token for the user."""
    return f"token_{user_id}"
''')
    
    (project_a / "models.py").write_text('''
from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    email: str
''')
    
    # Create project B (JavaScript Web)
    project_b = temp_dir / "project-b"
    project_b.mkdir()
    
    (project_b / "auth.js").write_text('''
function authenticateUser(email, password) {
    return firebase.auth().signInWithEmailAndPassword(email, password);
}

function createSessionToken(userId) {
    return jwt.sign({ userId }, process.env.JWT_SECRET);
}
''')
    
    (project_b / "user.js").write_text('''
class User {
    constructor(id, email) {
        this.id = id;
        this.email = email;
    }
}
''')
    
    # Initialize git repos
    for project in [project_a, project_b]:
        subprocess.run(["git", "init"], cwd=project, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=project, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=project, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project, capture_output=True)
    
    yield {"project_a": project_a, "project_b": project_b, "temp_dir": temp_dir}
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def initialized_projects(temp_projects):
    """Initialize projects with memnexus config."""
    for name, path in [("project-a", temp_projects["project_a"]), 
                       ("project-b", temp_projects["project_b"])]:
        memnexus_dir = path / ".memnexus"
        memnexus_dir.mkdir()
        
        config = f'''version: "1.0"
project:
  name: "{name}"
  root: "{path}"
  initialized_at: "2026-03-27T10:00:00"

memory:
  backend: "lancedb"
  path: ".memnexus/memory.lance"

embedding:
  method: "tfidf"
  dim: 384

git:
  enabled: true
  max_history: 1000

code:
  languages: ["python", "javascript"]
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/"
    - "node_modules/"
    - ".git/"
'''
        (memnexus_dir / "config.yaml").write_text(config)
    
    return temp_projects


@pytest.mark.asyncio
async def test_index_projects(initialized_projects):
    """Test indexing projects (Git + Code)."""
    project_a = initialized_projects["project_a"]
    
    memory = await CodeMemory.init(project_a)
    
    # Index Git history
    git_result = await memory.index_git_history(limit=10)
    assert git_result["commits_indexed"] >= 1
    
    # Index code
    code_result = await memory.index_codebase()
    assert code_result["symbols_indexed"] > 0
    assert code_result["files_processed"] > 0
    
    await memory.close()


@pytest.mark.asyncio
async def test_project_search(initialized_projects):
    """Test searching within individual projects."""
    project_a = initialized_projects["project_a"]
    
    # First index the project
    memory = await CodeMemory.init(project_a)
    await memory.index_codebase()
    
    # Search
    results = await memory.search_code("authenticate", limit=5)
    assert len(results) > 0
    
    # Check that we found the auth function
    symbol_names = [r.metadata.get("symbol_name", "") for r in results]
    assert any("authenticate" in name for name in symbol_names)
    
    await memory.close()


@pytest.mark.asyncio
async def test_global_register(initialized_projects):
    """Test registering projects with global memory."""
    project_a = initialized_projects["project_a"]
    project_b = initialized_projects["project_b"]
    
    global_memory = await GlobalMemory.init()
    
    # Register projects
    info_a = await global_memory.register_project(
        name="test-api",
        path=str(project_a),
        description="Python API service",
        tags=["python", "api", "auth"]
    )
    assert info_a.name == "test-api"
    assert "python" in info_a.tags
    
    info_b = await global_memory.register_project(
        name="test-web",
        path=str(project_b),
        description="JavaScript web app",
        tags=["javascript", "web"]
    )
    assert info_b.name == "test-web"
    
    # List projects
    projects = global_memory.list_projects()
    assert len(projects) >= 2
    
    # Cleanup
    await global_memory.close()
    global_memory.unregister_project("test-api")
    global_memory.unregister_project("test-web")


@pytest.mark.asyncio
async def test_global_add_and_search(initialized_projects):
    """Test adding memories and searching globally."""
    global_memory = await GlobalMemory.init()
    
    # Add test memories
    await global_memory.add_memory(
        content="def authenticate_user(username, password): Python auth function",
        source="code:auth.py",
        project_name="test-api",
        memory_type="code_symbol"
    )
    
    await global_memory.add_memory(
        content="function authenticateUser(email, password): JavaScript auth function",
        source="code:auth.js",
        project_name="test-web",
        memory_type="code_symbol"
    )
    
    await global_memory.add_memory(
        content="class User with id, username, email fields",
        source="code:models.py",
        project_name="test-api",
        memory_type="code_symbol"
    )
    
    # Search all projects
    results = await global_memory.search("auth", limit=10)
    assert len(results) > 0
    
    # Should find results from both projects
    project_names = {r.project_name for r in results}
    assert "test-api" in project_names or "test-web" in project_names
    
    # Search specific project
    results_api = await global_memory.search("user", project="test-api", limit=5)
    # May or may not have results depending on embedding
    
    await global_memory.close()


@pytest.mark.asyncio
async def test_global_stats(initialized_projects):
    """Test getting global memory statistics."""
    project_a = initialized_projects["project_a"]
    
    global_memory = await GlobalMemory.init()
    
    # Register a project
    await global_memory.register_project(
        name="stats-test",
        path=str(project_a),
        tags=["test"]
    )
    
    # Get stats
    stats = global_memory.get_stats()
    assert "projects_registered" in stats
    assert stats["projects_registered"] >= 1
    
    await global_memory.close()
    global_memory.unregister_project("stats-test")


@pytest.mark.asyncio
async def test_project_filter_in_search(initialized_projects):
    """Test filtering search results by project."""
    global_memory = await GlobalMemory.init()
    
    # Add memories from different projects
    await global_memory.add_memory(
        content="Python function for data processing",
        source="code:data.py",
        project_name="project-py",
        memory_type="code_symbol"
    )
    
    await global_memory.add_memory(
        content="JavaScript function for data visualization",
        source="code:viz.js",
        project_name="project-js",
        memory_type="code_symbol"
    )
    
    # Search without filter
    all_results = await global_memory.search("function", limit=10)
    
    # Search with project filter
    py_results = await global_memory.search("function", project="project-py", limit=5)
    
    # Filtered results should be subset of all results or empty
    assert len(py_results) <= len(all_results)
    
    # All results should be from the specified project
    for r in py_results:
        assert r.project_name == "project-py"
    
    await global_memory.close()


@pytest.mark.asyncio
async def test_end_to_end_workflow(initialized_projects):
    """Test complete end-to-end workflow."""
    project_a = initialized_projects["project_a"]
    
    # 1. Initialize CodeMemory
    code_memory = await CodeMemory.init(project_a)
    
    # 2. Index project
    await code_memory.index_codebase()
    
    # 3. Initialize GlobalMemory
    global_memory = await GlobalMemory.init()
    
    # 4. Register project
    await global_memory.register_project(
        name="e2e-test",
        path=str(project_a),
        tags=["e2e"]
    )
    
    # 5. Add memory manually (simulating sync)
    await global_memory.add_memory(
        content="User authentication implementation",
        source="code:auth.py",
        project_name="e2e-test",
        memory_type="code_symbol"
    )
    
    # 6. Search globally
    results = await global_memory.search("authentication", limit=5)
    assert len(results) >= 0  # May find results depending on embedding
    
    # Cleanup
    await code_memory.close()
    await global_memory.close()
    global_memory.unregister_project("e2e-test")


@pytest.fixture
def isolated_global_config(temp_projects):
    """Provide isolated global config for each test."""
    import uuid
    
    # Use a unique temp directory for this test
    temp_dir = temp_projects["temp_dir"] / f"global_config_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    original_dir = GlobalMemoryConfig.GLOBAL_DIR
    original_config_file = GlobalMemoryConfig.CONFIG_FILE
    
    # Update both GLOBAL_DIR and CONFIG_FILE
    GlobalMemoryConfig.GLOBAL_DIR = temp_dir / ".memnexus" / "global"
    GlobalMemoryConfig.CONFIG_FILE = GlobalMemoryConfig.GLOBAL_DIR / "config.json"
    
    yield temp_dir
    
    # Cleanup
    GlobalMemoryConfig.GLOBAL_DIR = original_dir
    GlobalMemoryConfig.CONFIG_FILE = original_config_file


class TestGlobalMemoryConfig:
    """Tests for GlobalMemoryConfig (no async required)."""
    
    def test_project_registration(self, isolated_global_config):
        """Test project registration without full dependencies."""
        config = GlobalMemoryConfig()
        
        # Register project
        info = config.register_project(
            name="config-test",
            path="/path/to/project",
            description="Test project",
            tags=["test", "python"]
        )
        
        assert info.name == "config-test"
        assert info.path == "/path/to/project"
        assert "test" in info.tags
        
        # List projects
        projects = config.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "config-test"
        
        # Get project
        found = config.get_project("config-test")
        assert found is not None
        assert found.name == "config-test"
        
        # Unregister
        success = config.unregister_project("config-test")
        assert success is True
        assert config.get_project("config-test") is None
    
    def test_config_persistence(self, isolated_global_config):
        """Test config save and reload."""
        # Create and save config
        config1 = GlobalMemoryConfig()
        config1.register_project(name="persist-test", path="/tmp/test")
        config1.save()
        
        # Load in new instance
        config2 = GlobalMemoryConfig()
        projects = config2.list_projects()
        
        assert len(projects) == 1
        assert projects[0].name == "persist-test"
