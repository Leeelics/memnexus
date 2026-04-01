# Session Explorer Requirements Specification

> **Document Version:** 1.0  
> **Target Release:** memnexus v0.4.0  
> **Related Project:** kimi-tachi v0.5.3+  
> **Status:** Draft

---

## 1. Executive Summary

This document specifies the requirements for the **Session Explorer** feature in memnexus, which enables proactive exploration of historical sessions to discover relevant context across conversation boundaries.

### 1.1 Background

kimi-tachi v0.5.3 implemented a temporary Session Explorer to solve the problem of discovering relevant decisions from other sessions. This functionality should be migrated to memnexus as the canonical storage layer.

### 1.2 Goals

- Enable cross-session context discovery
- Provide efficient deduplication of decisions
- Offer relevance-based ranking of historical sessions
- Support incremental exploration with exploration tracking

### 1.3 Non-Goals

- Real-time synchronization between sessions
- Distributed session storage
- Natural language generation of summaries

---

## 2. Functional Requirements

### 2.1 Session Exploration (FR-SE-001)

**FR-SE-001.1** The system SHALL provide a method to explore historical sessions based on a query string.

```python
async def explore_related(
    current_session_id: str,
    query: str,
    context: dict,
    options: ExploreOptions
) -> ExplorationResult
```

**FR-SE-001.2** The exploration SHALL exclude the current session from results.

**FR-SE-001.3** The exploration SHALL respect a minimum relevance threshold (0.0-1.0).

**FR-SE-001.4** The exploration SHALL return a maximum number of decisions as specified by the limit parameter.

**FR-SE-001.5** The system SHALL skip sessions that have already been explored by the current session.

### 2.2 Decision Deduplication (FR-DD-001)

**FR-DD-001.1** The system SHALL provide content-based deduplication of decisions.

**FR-DD-001.2** The deduplication SHALL use semantic fingerprinting (not exact string matching).

**FR-DD-001.3** The fingerprinting algorithm SHALL:
- Extract keywords from content
- Normalize text (lowercase, remove punctuation)
- Generate a hash-based fingerprint
- Store fingerprints with metadata

**FR-DD-001.4** The system SHALL provide a method to check if content is a duplicate:

```python
async def check_duplicate(
    content: str,
    context: dict = None
) -> DuplicateCheckResult
```

**FR-DD-001.5** The duplicate check SHALL return:
- `is_duplicate`: Boolean
- `confidence`: Float (0.0-1.0)
- `similar_decisions`: List of similar existing decisions

### 2.3 Relevance Scoring (FR-RS-001)

**FR-RS-001.1** The system SHALL calculate relevance scores for sessions based on:
- Keyword overlap between query and session decisions
- Project/working directory matching
- Temporal proximity (time decay)

**FR-RS-001.2** The scoring formula SHALL be:

```
score = (keyword_matches × 0.3) 
        + (same_project ? 1.0 : 0) 
        + (related_path ? 0.5 : 0)
        × time_decay_factor

time_decay_factor = 1.0 / (1.0 + age_in_days / 7)
```

**FR-RS-001.3** The system SHALL support configurable weights for scoring factors.

**FR-RS-001.4** Relevance scores SHALL be normalized to 0.0-1.0 range.

### 2.4 Exploration Tracking (FR-ET-001)

**FR-ET-001.1** The system SHALL track which sessions have been explored by which sessions.

**FR-ET-001.2** Each exploration record SHALL include:
- Source session ID (the explorer)
- Target session ID (the explored)
- Timestamp of exploration
- Relevance score at time of exploration
- Number of decisions extracted

**FR-ET-001.3** The system SHALL provide a method to check if a session has been explored:

```python
def is_explored(
    session_id: str,
    by_session: Optional[str] = None
) -> bool
```

**FR-ET-001.4** The system SHALL support marking a session as explored:

```python
async def mark_explored(
    session_id: str,
    by_session: str,
    relevance: float,
    decisions_count: int
) -> None
```

### 2.5 Storage and Persistence (FR-SP-001)

**FR-SP-001.1** Decision fingerprints SHALL be persisted to storage.

**FR-SP-001.2** Exploration records SHALL be persisted to storage.

**FR-SP-001.3** The system SHALL support atomic updates to exploration state.

**FR-SP-001.4** Storage format SHALL be JSON for human readability.

---

## 3. Interface Requirements

### 3.1 Public API

#### 3.1.1 SessionExplorer Class

```python
class SessionExplorer:
    """
    Main interface for session exploration functionality.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        config: Optional[ExplorerConfig] = None
    ):
        """
        Initialize the SessionExplorer.
        
        Args:
            storage_path: Path to store exploration data
            config: Configuration options
        """
    
    async def explore_related(
        self,
        current_session_id: str,
        query: str,
        context: Optional[dict] = None,
        limit: int = 5,
        min_relevance: float = 0.2
    ) -> ExplorationResult:
        """
        Explore historical sessions for relevant decisions.
        
        Args:
            current_session_id: ID of the current session (excluded from results)
            query: Search query string
            context: Additional context (cwd, project, etc.)
            limit: Maximum number of decisions to return
            min_relevance: Minimum relevance threshold (0.0-1.0)
            
        Returns:
            ExplorationResult containing decisions and metadata
        """
    
    async def mark_explored(
        self,
        session_id: str,
        by_session: str,
        relevance: float = 0.0,
        decisions_count: int = 0
    ) -> None:
        """Mark a session as having been explored."""
    
    def is_explored(
        self,
        session_id: str,
        by_session: Optional[str] = None
    ) -> bool:
        """Check if a session has been explored."""
    
    def get_stats(self) -> ExplorationStats:
        """Get exploration statistics."""
```

#### 3.1.2 DecisionDeduplicator Class

```python
class DecisionDeduplicator:
    """
    Content-based deduplication for decisions.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the deduplicator."""
    
    async def check_duplicate(
        self,
        content: str,
        context: Optional[dict] = None
    ) -> DuplicateCheckResult:
        """
        Check if content is a duplicate.
        
        Returns:
            DuplicateCheckResult with is_duplicate, confidence, similar_items
        """
    
    async def add_fingerprint(
        self,
        content: str,
        source_session: str = "",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add a fingerprint for content.
        
        Returns:
            The fingerprint hash
        """
    
    def get_all_keywords(self) -> Set[str]:
        """Get all known keywords from fingerprints."""
```

#### 3.1.3 RelevanceScorer Class

```python
class RelevanceScorer:
    """
    Calculates relevance scores between sessions and queries.
    """
    
    def __init__(self, config: Optional[ScorerConfig] = None):
        """Initialize with optional custom weights."""
    
    def calculate(
        self,
        session_data: dict,
        query: str,
        context: Optional[dict] = None
    ) -> float:
        """
        Calculate relevance score.
        
        Returns:
            Score between 0.0 and 1.0
        """
```

### 3.2 Data Models

#### 3.2.1 ExplorationResult

```python
@dataclass
class ExplorationResult:
    decisions: List[Decision]
    explored_sessions: List[str]
    total_relevance: float
    query: str
    timestamp: str
```

#### 3.2.2 Decision

```python
@dataclass
class Decision:
    content: str
    timestamp: str
    source_session: str
    fingerprint: Optional[str]
    metadata: Optional[dict]
```

#### 3.2.3 DuplicateCheckResult

```python
@dataclass
class DuplicateCheckResult:
    is_duplicate: bool
    confidence: float
    similar_decisions: List[Decision]
    fingerprint: Optional[str]
```

#### 3.2.4 ExplorationStats

```python
@dataclass
class ExplorationStats:
    total_explored_sessions: int
    total_unique_decisions: int
    known_keywords_count: int
    available_session_files: int
```

---

## 4. Performance Requirements

### 4.1 Response Time (PR-RT-001)

**PR-RT-001.1** Session exploration SHALL complete within 500ms for up to 100 sessions.

**PR-RT-001.2** Duplicate checking SHALL complete within 10ms.

**PR-RT-001.3** Relevance scoring SHALL complete within 5ms per session.

### 4.2 Storage (PR-ST-001)

**PR-ST-001.1** Storage overhead per decision fingerprint SHALL be < 500 bytes.

**PR-ST-001.2** Storage overhead per exploration record SHALL be < 200 bytes.

**PR-ST-001.3** Memory usage for loaded state SHALL scale linearly with number of fingerprints.

### 4.3 Concurrency (PR-CO-001)

**PR-CO-001.1** The system SHALL support concurrent read operations.

**PR-CO-001.2** Write operations SHALL be atomic (file-level locking acceptable for v1).

---

## 5. Integration Requirements

### 5.1 kimi-tachi Integration (IR-KT-001)

**IR-KT-001.1** The API SHALL be compatible with kimi-tachi's MemoryAdapter interface.

**IR-KT-001.2** Default storage paths SHALL align with kimi-tachi conventions.

**IR-KT-001.3** The system SHALL provide synchronous wrappers for async methods (for use in sync contexts).

Example integration:

```python
# In kimi-tachi
from memnexus import SessionExplorer, DecisionDeduplicator

class MemoryAdapter:
    def __init__(self):
        self._explorer = SessionExplorer()
        self._deduplicator = DecisionDeduplicator()
    
    async def explore_sessions(self, ...):
        return await self._explorer.explore_related(...)
```

### 5.2 Storage Backend (IR-SB-001)

**IR-SB-001.1** The system SHALL use SQLite for production deployments.

**IR-SB-001.2** The system SHALL support JSON file fallback for development.

**IR-SB-001.3** Storage backend SHALL be configurable via constructor parameter.

---

## 6. Storage Format

### 6.1 Decision Fingerprints

```json
{
  "fingerprints": {
    "a1b2c3d4e5f67890": {
      "hash": "a1b2c3d4e5f67890",
      "keywords": ["postgresql", "database", "user"],
      "timestamp": "2026-04-01T10:30:00",
      "source_session": "session_abc123",
      "content_preview": "Use PostgreSQL for user data..."
    }
  },
  "metadata": {
    "version": "1.0",
    "created_at": "2026-04-01T00:00:00"
  }
}
```

### 6.2 Exploration Records

```json
{
  "explorations": {
    "session_abc123": {
      "session_id": "session_abc123",
      "explored_at": "2026-04-01T14:00:00",
      "explored_by": "session_xyz789",
      "relevance_score": 0.85,
      "decisions_extracted": 3
    }
  }
}
```

---

## 7. Configuration

### 7.1 ExplorerConfig

```python
@dataclass
class ExplorerConfig:
    # Scoring weights
    keyword_match_weight: float = 0.3
    same_project_weight: float = 1.0
    related_path_weight: float = 0.5
    
    # Time decay
    time_decay_half_life_days: int = 7
    
    # Limits
    max_decisions_per_session: int = 20
    max_total_decisions: int = 100
    
    # Storage
    storage_backend: str = "auto"  # "sqlite", "json", "auto"
```

### 7.2 ScorerConfig

```python
@dataclass
class ScorerConfig:
    keyword_weight: float = 0.3
    project_weight: float = 1.0
    path_weight: float = 0.5
    time_decay: float = 7.0  # half-life in days
```

---

## 8. Error Handling

### 8.1 Error Types

```python
class SessionExplorerError(Exception):
    """Base exception for Session Explorer."""
    pass

class StorageError(SessionExplorerError):
    """Storage operation failed."""
    pass

class InvalidSessionError(SessionExplorerError):
    """Session data is invalid or corrupted."""
    pass

class ConfigurationError(SessionExplorerError):
    """Invalid configuration."""
    pass
```

### 8.2 Error Handling Requirements

**ER-EH-001** The system SHALL NOT raise exceptions for non-critical errors during exploration.

**ER-EH-002** The system SHALL return empty results with error metadata on failure.

**ER-EH-003** The system SHALL log errors for debugging purposes.

---

## 9. Testing Requirements

### 9.1 Unit Tests (TR-UT-001)

**TR-UT-001.1** Decision fingerprinting SHALL have > 95% code coverage.

**TR-UT-001.2** Relevance scoring SHALL have > 90% code coverage.

**TR-UT-001.3** Deduplication SHALL have > 95% code coverage.

### 9.2 Integration Tests (TR-IT-001)

**TR-IT-001.1** End-to-end exploration flow SHALL be tested with real session files.

**TR-IT-001.2** Concurrent access patterns SHALL be tested.

**TR-IT-001.3** Storage backend switching SHALL be tested.

### 9.3 Performance Tests (TR-PT-001)

**TR-PT-001.1** Response time requirements SHALL be validated with 100+ sessions.

**TR-PT-001.2** Memory usage SHALL be profiled with 1000+ fingerprints.

---

## 10. Migration Path

### 10.1 From kimi-tachi Temporary Implementation

| Component | kimi-tachi Location | memnexus Target |
|-----------|--------------------|-----------------|
| SessionExplorer | `session_explorer.py` | `memnexus.session.SessionExplorer` |
| DecisionDeduplicator | `session_explorer.py` | `memnexus.decision.Deduplicator` |
| RelevanceScorer | `session_explorer.py` | `memnexus.relevance.Scorer` |
| Fingerprint storage | `~/.kimi-tachi/memory/session_explorer/` | `~/.memnexus/explorer/` |

### 10.2 Migration Steps

1. Implement SessionExplorer in memnexus v0.4.0
2. Implement DecisionDeduplicator in memnexus v0.4.0
3. Add compatibility layer in kimi-tachi v0.6.0
4. Deprecate kimi-tachi temporary implementations
5. Remove kimi-tachi fallback code in v0.7.0

---

## 11. Open Questions

1. Should we support vector-based semantic similarity in addition to keyword matching?
2. Should exploration be triggered automatically or only on explicit request?
3. How should we handle session archival/migration?
4. Should we support distributed/multi-device session synchronization?

---

## 12. Appendix

### 12.1 Glossary

| Term | Definition |
|------|------------|
| Session | A conversation context with a unique ID |
| Decision | A recorded conclusion or choice made during a session |
| Fingerprint | A hash-based signature of decision content |
| Exploration | The process of scanning historical sessions for relevant context |
| Relevance Score | A 0.0-1.0 score indicating how relevant a session is to a query |

### 12.2 References

- kimi-tachi v0.5.3 Session Explorer: `kimi-tachi/src/kimi_tachi/memory/session_explorer.py`
- kimi-tachi Architecture Doc: `kimi-tachi/docs/ARCHITECTURE_REFACTOR_V053.md`
- memnexus Current API: `memnexus/docs/API.md`

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | kimi-tachi Team | Initial specification based on v0.5.3 implementation |

---

*This document is a living specification. Please update as requirements evolve.*
