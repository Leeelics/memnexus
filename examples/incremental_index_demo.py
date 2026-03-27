"""Demo script for incremental indexing feature.

This script demonstrates how incremental indexing works in MemNexus.
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memnexus.memory.index_state import IndexStateManager, IndexState


async def demo_index_state():
    """Demonstrate index state management."""
    
    # Create a temporary project for demo
    demo_project = Path("./demo_project")
    demo_project.mkdir(exist_ok=True)
    
    # Create .memnexus directory
    (demo_project / ".memnexus").mkdir(exist_ok=True)
    
    # Initialize index state manager
    state_mgr = IndexStateManager(demo_project)
    
    print("=" * 60)
    print("MemNexus Incremental Indexing Demo")
    print("=" * 60)
    
    # 1. Show initial state
    print("\n1. Initial State:")
    state = state_mgr.load_state()
    print(f"   Project: {state.project_path}")
    print(f"   Created: {state.created_at}")
    print(f"   Git commits indexed: {len(state.git_state.indexed_commits) if state.git_state else 0}")
    print(f"   Files tracked: {len(state.file_states)}")
    
    # 2. Simulate indexing some files
    print("\n2. Simulating File Indexing:")
    
    # Create a test file
    test_file = demo_project / "test.py"
    test_file.write_text("def hello():\n    return 'world'\n")
    
    # Check if should index
    rel_path = "test.py"
    should_index = state_mgr.should_index_file(rel_path)
    print(f"   Should index '{rel_path}': {should_index}")
    
    # Update file state (simulating successful indexing)
    state_mgr.update_file_state(rel_path, symbol_count=1)
    print(f"   Indexed '{rel_path}' with 1 symbol")
    
    # Check again - should not need re-index
    should_index = state_mgr.should_index_file(rel_path)
    print(f"   Should re-index '{rel_path}': {should_index}")
    
    # 3. Simulate modifying the file
    print("\n3. Simulating File Modification:")
    import time
    time.sleep(0.1)  # Small delay to ensure different timestamp
    test_file.write_text("def hello():\n    return 'world'\n\ndef goodbye():\n    return 'see ya'\n")
    
    should_index = state_mgr.should_index_file(rel_path)
    print(f"   Should re-index after modification: {should_index}")
    
    # Update state again
    state_mgr.update_file_state(rel_path, symbol_count=2)
    print(f"   Re-indexed '{rel_path}' with 2 symbols")
    
    # 4. Simulate Git indexing
    print("\n4. Simulating Git Indexing:")
    state_mgr.update_git_state(
        last_commit_hash="abc123",
        last_commit_timestamp="2026-03-27T10:00:00",
        new_commits=["abc123", "def456"],
        total_indexed=2
    )
    print(f"   Indexed 2 commits: abc123, def456")
    
    # Check unindexed commits
    all_commits = ["abc123", "def456", "ghi789"]
    unindexed = state_mgr.get_unindexed_commits(all_commits)
    print(f"   Unindexed commits: {unindexed}")
    
    # 5. Show final stats
    print("\n5. Final Statistics:")
    stats = state_mgr.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    import shutil
    shutil.rmtree(demo_project)
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_index_state())
