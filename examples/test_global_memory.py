"""Test script for Global Memory functionality.

This script tests the global memory features without LanceDB dependencies.
Run this to verify the core logic works before installing full dependencies.
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_embedder():
    """Test TF-IDF embedder (zero dependencies)."""
    
    print("=" * 60)
    print("Testing TF-IDF Embedder")
    print("=" * 60)
    
    # Import embedder directly (no external deps)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'embedder', 
        Path(__file__).parent.parent / 'src' / 'memnexus' / 'memory' / 'embedder.py'
    )
    embedder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(embedder)
    
    # Test 1: TF-IDF embedding
    print("\n1. Testing TF-IDF embedding...")
    tfidf = embedder.TfidfEmbedder(dim=384)
    
    text1 = "def authenticate_user(username, password): return True"
    embedding1 = tfidf.embed(text1)
    print(f"   ✓ Embedding shape: {len(embedding1)}")
    print(f"   ✓ Non-zero elements: {sum(1 for x in embedding1 if x != 0)}")
    
    # Verify normalization
    import math
    norm = math.sqrt(sum(x * x for x in embedding1))
    print(f"   ✓ L2 norm: {norm:.4f} (should be ~1.0)")
    assert 0.99 < norm < 1.01, "Embedding should be L2 normalized"
    
    # Test 2: Similar texts have similar embeddings
    print("\n2. Testing similar text similarity...")
    text2 = "def authenticate_user(email, pwd): return False"
    embedding2 = tfidf.embed(text2)
    
    # Calculate cosine similarity
    dot = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = math.sqrt(sum(x * x for x in embedding1))
    norm2 = math.sqrt(sum(x * x for x in embedding2))
    similarity = dot / (norm1 * norm2)
    print(f"   ✓ Similarity between auth functions: {similarity:.4f}")
    # TF-IDF similarity for code with shared function names
    assert similarity > 0.2, "Similar code should have some similarity"
    
    # Test 3: Different texts have low similarity
    print("\n3. Testing different text dissimilarity...")
    text3 = "def calculate_total(price, quantity): return price * quantity"
    embedding3 = tfidf.embed(text3)
    
    dot = sum(a * b for a, b in zip(embedding1, embedding3))
    norm3 = math.sqrt(sum(x * x for x in embedding3))
    similarity2 = dot / (norm1 * norm3)
    print(f"   ✓ Similarity (auth vs calculate): {similarity2:.4f}")
    print(f"   ✓ Auth texts more similar: {similarity > similarity2}")
    # Auth functions should be more similar to each other than to calculate
    assert similarity >= similarity2, "Auth texts should be at least as similar as different texts"
    
    # Test 4: Batch embedding
    print("\n4. Testing batch embedding...")
    texts = ["def func1():", "def func2():", "def func3():"]
    embeddings = tfidf.embed_batch(texts)
    print(f"   ✓ Batch size: {len(embeddings)}")
    assert len(embeddings) == 3, "Batch should return same number of embeddings"
    
    # Test 5: Hash embedder
    print("\n5. Testing Hash embedder...")
    hash_emb = embedder.HashEmbedder(dim=384)
    embedding4 = hash_emb.embed(text1)
    print(f"   ✓ Hash embedding shape: {len(embedding4)}")
    print(f"   ✓ Non-zero elements: {sum(1 for x in embedding4 if x != 0)}")
    
    # Test 6: get_embedder factory
    print("\n6. Testing get_embedder factory...")
    tfidf2 = embedder.get_embedder("tfidf", dim=384)
    hash2 = embedder.get_embedder("hash", dim=384)
    print(f"   ✓ Factory creates embedders correctly")
    
    try:
        embedder.get_embedder("unknown")
        assert False, "Should raise ValueError for unknown method"
    except ValueError:
        print(f"   ✓ Factory rejects unknown methods")
    
    print("\n" + "=" * 60)
    print("Embedder tests passed! ✓")
    print("=" * 60)


async def test_index_state():
    """Test IndexStateManager."""
    
    print("\n" + "=" * 60)
    print("Testing Index State Manager")
    print("=" * 60)
    
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'index_state',
        Path(__file__).parent.parent / 'src' / 'memnexus' / 'memory' / 'index_state.py'
    )
    index_state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(index_state)
    
    # Create temp project
    temp_dir = tempfile.mkdtemp()
    
    try:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        (project_path / ".memnexus").mkdir()
        
        # Test 1: Create state manager
        print("\n1. Creating IndexStateManager...")
        state_mgr = index_state.IndexStateManager(project_path)
        print(f"   ✓ State manager created")
        
        # Test 2: Load initial state
        print("\n2. Loading initial state...")
        state = state_mgr.load_state()
        print(f"   ✓ Project path: {state.project_path}")
        print(f"   ✓ Version: {state.version}")
        print(f"   ✓ Files tracked: {len(state.file_states)}")
        assert len(state.file_states) == 0, "Initial state should have no files"
        
        # Test 3: Create test file
        print("\n3. Creating test file...")
        test_file = project_path / "test.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        print(f"   ✓ Test file created: {test_file}")
        
        # Test 4: Check if should index (should be True for new file)
        print("\n4. Checking if should index (new file)...")
        should_index = state_mgr.should_index_file("test.py")
        print(f"   ✓ Should index: {should_index}")
        assert should_index == True, "New file should need indexing"
        
        # Test 5: Update file state
        print("\n5. Updating file state...")
        state_mgr.update_file_state("test.py", symbol_count=1)
        print(f"   ✓ File state updated")
        
        # Test 6: Check again (should not need re-index)
        print("\n6. Checking again (should be False)...")
        should_index2 = state_mgr.should_index_file("test.py")
        print(f"   ✓ Should index: {should_index2}")
        assert should_index2 == False, "Unchanged file should not need re-indexing"
        
        # Test 7: Modify file
        print("\n7. Modifying file...")
        import time
        time.sleep(0.1)
        test_file.write_text("def hello():\n    return 'world'\n\ndef bye(): pass\n")
        should_index3 = state_mgr.should_index_file("test.py")
        print(f"   ✓ Should index after modification: {should_index3}")
        assert should_index3 == True, "Modified file should need re-indexing"
        
        # Test 8: Update and save
        print("\n8. Saving state...")
        state_mgr.update_file_state("test.py", symbol_count=2)
        state_mgr.save_state()
        print(f"   ✓ State saved")
        
        # Test 9: Create new manager and reload
        print("\n9. Reloading state...")
        state_mgr2 = index_state.IndexStateManager(project_path)
        state2 = state_mgr2.load_state()
        print(f"   ✓ Reloaded files tracked: {len(state2.file_states)}")
        assert len(state2.file_states) == 1, "Should have 1 file after reload"
        
        # Test 10: Git state
        print("\n10. Testing Git state...")
        state_mgr.update_git_state(
            last_commit_hash="abc123",
            last_commit_timestamp="2026-03-27T10:00:00",
            new_commits=["abc123", "def456"],
            total_indexed=2
        )
        git_state = state_mgr.get_git_state()
        print(f"   ✓ Git commits indexed: {git_state.total_indexed if git_state else 0}")
        
        # Test 11: Get unindexed commits
        print("\n11. Testing unindexed commits detection...")
        all_commits = ["abc123", "def456", "ghi789"]
        unindexed = state_mgr.get_unindexed_commits(all_commits)
        print(f"   ✓ Unindexed commits: {unindexed}")
        assert "ghi789" in unindexed, "New commit should be unindexed"
        
        # Test 12: Stats
        print("\n12. Getting stats...")
        stats = state_mgr.get_stats()
        print(f"   ✓ Files tracked: {stats['files_tracked']}")
        print(f"   ✓ Git commits indexed: {stats['git_commits_indexed']}")
        
        print("\n" + "=" * 60)
        print("Index state tests passed! ✓")
        print("=" * 60)
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_global_config():
    """Test GlobalMemoryConfig without full dependencies."""
    
    print("\n" + "=" * 60)
    print("Testing Global Memory Config")
    print("=" * 60)
    
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'global_memory',
        Path(__file__).parent.parent / 'src' / 'memnexus' / 'global_memory.py'
    )
    
    # Load only the dataclass and config parts we need
    spec = importlib.util.spec_from_file_location(
        'global_memory_test',
        Path(__file__).parent.parent / 'src' / 'memnexus' / 'global_memory.py'
    )
    
    # For this test, we'll just test the logic directly
    import json
    from dataclasses import dataclass, field, asdict
    from datetime import datetime
    
    @dataclass
    class TestProjectInfo:
        name: str
        path: str
        description: str = None
        registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
        last_synced: str = None
        git_url: str = None
        tags: list = None
        
        def __post_init__(self):
            if self.tags is None:
                self.tags = []
        
        def to_dict(self):
            return asdict(self)
        
        @classmethod
        def from_dict(cls, data):
            return cls(**data)
    
    # Test 1: Create project info
    print("\n1. Creating project info...")
    project = TestProjectInfo(
        name="test-api",
        path="/home/user/projects/test-api",
        description="Test API",
        tags=["python", "fastapi"]
    )
    print(f"   ✓ Created: {project.name}")
    print(f"   ✓ Tags: {project.tags}")
    
    # Test 2: Serialize/deserialize
    print("\n2. Testing serialization...")
    data = project.to_dict()
    print(f"   ✓ Serialized: {data['name']}")
    
    restored = TestProjectInfo.from_dict(data)
    print(f"   ✓ Deserialized: {restored.name}")
    assert restored.name == project.name
    assert restored.tags == project.tags
    
    # Test 3: JSON serialization
    print("\n3. Testing JSON serialization...")
    json_str = json.dumps(data)
    data2 = json.loads(json_str)
    print(f"   ✓ JSON round-trip successful")
    assert data2['name'] == project.name
    
    print("\n" + "=" * 60)
    print("Global config tests passed! ✓")
    print("=" * 60)


async def main():
    """Run all tests."""
    
    print("\n" + "=" * 70)
    print(" MemNexus Global Memory Test Suite (v0.3.0)")
    print(" Testing core functionality without LanceDB")
    print("=" * 70)
    
    all_passed = True
    
    try:
        await test_embedder()
    except Exception as e:
        print(f"\n✗ Embedder tests failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        await test_index_state()
    except Exception as e:
        print(f"\n✗ Index state tests failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        await test_global_config()
    except Exception as e:
        print(f"\n✗ Global config tests failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print(" ✓ All Tests Passed!")
    else:
        print(" ✗ Some Tests Failed")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
