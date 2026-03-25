#!/usr/bin/env python3
"""
Week 3 Completion Test - Code Parsing Integration

This script verifies that Week 3 code parsing is working correctly.
It tests the CodeParser, CodeChunker, and validates the implementation.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly from code.py to avoid loading other modules
import importlib.util
spec = importlib.util.spec_from_file_location("code", 
    str(Path(__file__).parent.parent / "src" / "memnexus" / "memory" / "code.py"))
code_module = importlib.util.module_from_spec(spec)
sys.modules["code_module"] = code_module
spec.loader.exec_module(code_module)

CodeParser = code_module.CodeParser
CodeChunker = code_module.CodeChunker
CodeMemoryExtractor = code_module.CodeMemoryExtractor
CodeSymbol = code_module.CodeSymbol
CodeChunk = code_module.CodeChunk
ImportInfo = code_module.ImportInfo


def create_test_python_file(tmpdir: Path) -> Path:
    """Create a test Python file with various code structures."""
    content = '''
"""Authentication module for the application.

This module handles user authentication and session management.
"""

from typing import Optional, Dict
from datetime import datetime
import hashlib


class AuthController:
    """Controller for authentication operations."""
    
    def __init__(self, db_connection: str):
        """Initialize the auth controller.
        
        Args:
            db_connection: Database connection string
        """
        self.db = db_connection
        self.sessions: Dict[str, dict] = {}
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user with username and password.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            User data if authenticated, None otherwise
        """
        # Hash the password
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        # Check against database
        user = self._find_user(username)
        if user and user['password_hash'] == hashed:
            return user
        return None
    
    def _find_user(self, username: str) -> Optional[dict]:
        """Find user by username."""
        # Database lookup
        return {"username": username, "password_hash": "abc123"}
    
    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


def create_auth_controller(db_url: str) -> AuthController:
    """Factory function to create AuthController.
    
    Args:
        db_url: Database URL
        
    Returns:
        Configured AuthController instance
    """
    return AuthController(db_url)


# Global instance
_default_controller: Optional[AuthController] = None


def get_default_controller() -> AuthController:
    """Get or create default auth controller."""
    global _default_controller
    if _default_controller is None:
        _default_controller = create_auth_controller("sqlite:///default.db")
    return _default_controller
'''
    
    file_path = tmpdir / "auth.py"
    file_path.write_text(content)
    return file_path


def test_code_parser():
    """Test CodeParser functionality."""
    
    print("=" * 70)
    print("WEEK 3: Code Parsing Test")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = create_test_python_file(Path(tmpdir))
        print(f"✓ Created test file: {file_path}")
        
        parser = CodeParser()
        
        # Test 1: Parse file
        print("\n[Test 1] Parse Python File")
        print("-" * 40)
        try:
            symbols = parser.parse_file(str(file_path))
            assert len(symbols) > 0, "Should find symbols"
            print(f"✓ Found {len(symbols)} symbols")
            
            for sym in symbols:
                print(f"  - {sym.symbol_type}: {sym.name} (lines {sym.start_line}-{sym.end_line})")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Check symbol types
        print("\n[Test 2] Symbol Types")
        print("-" * 40)
        try:
            classes = [s for s in symbols if s.symbol_type == "class"]
            functions = [s for s in symbols if s.symbol_type == "function"]
            methods = [s for s in symbols if s.symbol_type == "method"]
            
            assert len(classes) == 1, f"Expected 1 class, got {len(classes)}"
            assert len(functions) == 2, f"Expected 2 functions, got {len(functions)}"
            assert len(methods) == 4, f"Expected 4 methods, got {len(methods)}"
            
            print(f"✓ Classes: {len(classes)} (AuthController)")
            print(f"✓ Functions: {len(functions)} (create_auth_controller, get_default_controller)")
            print(f"✓ Methods: {len(methods)} (__init__, authenticate_user, _find_user, session_count)")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Symbol details
        print("\n[Test 3] Symbol Details")
        print("-" * 40)
        try:
            auth_controller = classes[0]
            assert auth_controller.name == "AuthController"
            assert "Controller for authentication" in (auth_controller.docstring or "")
            assert "class AuthController" in auth_controller.signature
            print(f"✓ Class: {auth_controller.name}")
            print(f"  Signature: {auth_controller.signature}")
            doc_preview = auth_controller.docstring[:50] if auth_controller.docstring else "None"
            print(f"  Docstring: {doc_preview}..." if auth_controller.docstring else "  Docstring: None")
            
            auth_method = [m for m in methods if m.name == "AuthController.authenticate_user"][0]
            assert "def authenticate_user" in auth_method.signature
            assert "username: str" in auth_method.signature
            assert "-> Optional[dict]" in auth_method.signature
            print(f"✓ Method: {auth_method.name}")
            print(f"  Signature: {auth_method.signature}")
            
            factory_func = [f for f in functions if f.name == "create_auth_controller"][0]
            assert "db_url: str" in factory_func.signature
            assert "-> AuthController" in factory_func.signature
            print(f"✓ Function: {factory_func.name}")
            print(f"  Signature: {factory_func.signature}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Extract imports
        print("\n[Test 4] Extract Imports")
        print("-" * 40)
        try:
            imports = parser.extract_imports(str(file_path))
            assert len(imports) == 3, f"Expected 3 imports, got {len(imports)}"
            print(f"✓ Found {len(imports)} imports")
            
            for imp in imports:
                print(f"  - {imp.module}: {imp.names}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Function calls extraction
        print("\n[Test 5] Extract Function Calls")
        print("-" * 40)
        try:
            content = '''
def test():
    result = hashlib.sha256(b"test").hexdigest()
    user = find_user("test")
    return result
'''
            calls = parser.extract_function_calls(content)
            print(f"✓ Found function calls: {calls}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL CODE PARSER TESTS PASSED!")
    print("=" * 70)
    return True


def test_code_chunker():
    """Test CodeChunker functionality."""
    
    print("\n" + "=" * 70)
    print("Code Chunker Test")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = create_test_python_file(Path(tmpdir))
        
        chunker = CodeChunker()
        
        # Test 1: Chunk file
        print("\n[Test 1] Chunk File")
        print("-" * 40)
        try:
            chunks = chunker.chunk_file(str(file_path))
            assert len(chunks) > 0, "Should create chunks"
            print(f"✓ Created {len(chunks)} chunks")
            
            for chunk in chunks:
                symbol_name = chunk.symbol.name if chunk.symbol else "Unknown"
                print(f"  - {chunk.chunk_type}: {symbol_name}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Chunk content
        print("\n[Test 2] Chunk Content")
        print("-" * 40)
        try:
            func_chunk = [c for c in chunks if c.chunk_type == "function"][0]
            assert func_chunk.symbol is not None
            assert func_chunk.context is not None
            assert "# File:" in func_chunk.context
            print(f"✓ Function chunk has context")
            print(f"  Context preview: {func_chunk.context[:100]}...")
            
            class_chunk = [c for c in chunks if c.chunk_type == "class"][0]
            assert class_chunk.symbol is not None
            print(f"✓ Class chunk has symbol: {class_chunk.symbol.name}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL CODE CHUNKER TESTS PASSED!")
    print("=" * 70)
    return True


def test_code_memory_extractor():
    """Test CodeMemoryExtractor functionality."""
    
    print("\n" + "=" * 70)
    print("Code Memory Extractor Test")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple files
        file1 = create_test_python_file(Path(tmpdir))
        
        file2_content = '''
"""Utils module."""

import json
from typing import Any

def serialize(data: Any) -> str:
    """Serialize data to JSON."""
    return json.dumps(data)

class DataStore:
    """Simple data store."""
    
    def save(self, key: str, value: Any) -> None:
        """Save a value."""
        pass
'''
        file2 = Path(tmpdir) / "utils.py"
        file2.write_text(file2_content)
        
        extractor = CodeMemoryExtractor()
        
        # Test 1: Extract from file
        print("\n[Test 1] Extract from File")
        print("-" * 40)
        try:
            chunks = extractor.extract_from_file(str(file1))
            assert len(chunks) > 0
            print(f"✓ Extracted {len(chunks)} chunks from {file1.name}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Extract from directory
        print("\n[Test 2] Extract from Directory")
        print("-" * 40)
        try:
            chunks_by_file = extractor.extract_from_directory(tmpdir, patterns=["*.py"])
            assert len(chunks_by_file) == 2, f"Expected 2 files, got {len(chunks_by_file)}"
            print(f"✓ Extracted from {len(chunks_by_file)} files")
            
            for file_path, chunks in chunks_by_file.items():
                print(f"  - {Path(file_path).name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: File summary
        print("\n[Test 3] File Summary")
        print("-" * 40)
        try:
            summary = extractor.get_file_summary(str(file1))
            assert summary["file_path"] == str(file1)
            assert summary["language"] == "python"
            assert summary["functions"] == 2
            assert summary["classes"] == 1
            assert summary["methods"] == 4
            
            print(f"✓ File summary:")
            print(f"  - Language: {summary['language']}")
            print(f"  - Functions: {summary['functions']}")
            print(f"  - Classes: {summary['classes']}")
            print(f"  - Methods: {summary['methods']}")
            print(f"  - Imports: {summary['imports']}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL CODE MEMORY EXTRACTOR TESTS PASSED!")
    print("=" * 70)
    return True


def main():
    """Run all Week 3 tests."""
    
    print("\n" + "=" * 70)
    print("WEEK 3: Code Parsing & Memory Integration")
    print("=" * 70)
    
    all_passed = True
    
    all_passed &= test_code_parser()
    all_passed &= test_code_chunker()
    all_passed &= test_code_memory_extractor()
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL WEEK 3 TESTS PASSED!")
        print("=" * 70)
        print("\nWeek 3 Deliverables:")
        print("  ✓ CodeParser class implemented")
        print("  ✓ Parse functions, classes, methods")
        print("  ✓ Extract imports")
        print("  ✓ Extract function calls")
        print("  ✓ CodeChunker for creating embeddable chunks")
        print("  ✓ CodeMemoryExtractor for batch processing")
        print("  ✓ CodeSymbol dataclass with full metadata")
        print("  ✓ CodeChunk with context preservation")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
