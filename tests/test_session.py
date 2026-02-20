"""Tests for session management."""

import pytest
from memnexus.core.session import (
    AgentConfig,
    AgentRole,
    AgentStatus,
    ExecutionStrategy,
    SessionManager,
    SessionStatus,
)


class TestSessionManager:
    """Test SessionManager."""
    
    @pytest.fixture
    async def manager(self):
        """Create session manager."""
        return SessionManager()
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test creating a session."""
        manager = SessionManager()
        
        session = await manager.create(
            name="Test Session",
            description="A test session",
            strategy=ExecutionStrategy.SEQUENTIAL,
        )
        
        assert session.name == "Test Session"
        assert session.description == "A test session"
        assert session.strategy == ExecutionStrategy.SEQUENTIAL
        assert session.status == SessionStatus.CREATED
        assert len(session.id) == 8
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting a session."""
        manager = SessionManager()
        
        session = await manager.create(name="Test Session")
        retrieved = await manager.get(session.id)
        
        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.name == "Test Session"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self):
        """Test getting a nonexistent session."""
        manager = SessionManager()
        
        retrieved = await manager.get("nonexistent")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing sessions."""
        manager = SessionManager()
        
        await manager.create(name="Session 1")
        await manager.create(name="Session 2")
        
        sessions = await manager.list_all()
        assert len(sessions) == 2
    
    @pytest.mark.asyncio
    async def test_add_agent(self):
        """Test adding agent to session."""
        manager = SessionManager()
        
        session = await manager.create(name="Test Session")
        config = AgentConfig(
            role=AgentRole.BACKEND,
            cli="claude",
        )
        
        agent = await manager.add_agent(session.id, config)
        
        assert agent is not None
        assert agent.session_id == session.id
        assert agent.config.role == AgentRole.BACKEND
        assert agent.config.cli == "claude"
        assert agent.status == AgentStatus.IDLE
    
    @pytest.mark.asyncio
    async def test_update_status(self):
        """Test updating session status."""
        manager = SessionManager()
        
        session = await manager.create(name="Test Session")
        success = await manager.update_status(
            session.id,
            SessionStatus.RUNNING,
        )
        
        assert success is True
        
        updated = await manager.get(session.id)
        assert updated.status == SessionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_delete_session(self):
        """Test deleting a session."""
        manager = SessionManager()
        
        session = await manager.create(name="Test Session")
        success = await manager.delete(session.id)
        
        assert success is True
        assert await manager.get(session.id) is None
