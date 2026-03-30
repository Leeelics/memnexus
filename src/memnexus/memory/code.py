"""Code parsing and extraction for memory indexing.

Week 3 Implementation: Tree-sitter based code parsing
- Parse Python code structure (functions, classes, imports)
- Extract code chunks for embedding
- Build simple call graph

Example:
    >>> from memnexus.memory.code import CodeParser
    >>> parser = CodeParser()
    >>> functions = parser.parse_file("auth.py")
    >>> for func in functions:
    ...     print(f"{func.name}: {func.start_line}-{func.end_line}")
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, method).

    Attributes:
        name: Symbol name
        symbol_type: 'function', 'class', 'method'
        content: Full source code
        signature: Function signature or class header
        docstring: Documentation string
        file_path: Source file path
        start_line: Start line number (1-indexed)
        end_line: End line number (1-indexed)
        language: Programming language
        metadata: Additional info (parameters, decorators, etc.)
    """

    name: str
    symbol_type: str  # 'function', 'class', 'method'
    content: str
    signature: str
    docstring: str | None
    file_path: str
    start_line: int
    end_line: int
    language: str = "python"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.symbol_type} {self.name} ({self.file_path}:{self.start_line}-{self.end_line})"
        )


@dataclass
class ImportInfo:
    """Represents an import statement."""

    module: str
    names: list[str]
    is_from_import: bool
    line: int


@dataclass
class CodeChunk:
    """A chunk of code for embedding.

    Attributes:
        content: The code content
        context: Surrounding context (imports, class context)
        symbol: Associated symbol if any
        language: Programming language
    """

    content: str
    context: str
    symbol: CodeSymbol | None
    language: str = "python"
    chunk_type: str = "function"  # 'function', 'class', 'module'


class CodeParser:
    """Parse code files using tree-sitter (Week 3).

    Currently uses AST-based parsing for Python.
    Will be extended to tree-sitter for multi-language support.

    Example:
        >>> parser = CodeParser()
        >>>
        >>> # Parse a file
        >>> symbols = parser.parse_file("src/auth.py")
        >>>
        >>> # Extract functions
        >>> functions = [s for s in symbols if s.symbol_type == "function"]
        >>>
        >>> # Get imports
        >>> imports = parser.extract_imports("src/auth.py")
    """

    def __init__(self):
        self._supported_languages = {"python", "javascript", "typescript"}

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
        }
        return mapping.get(ext, "unknown")

    def parse_file(self, file_path: str) -> list[CodeSymbol]:
        """Parse a file and extract all symbols.

        Args:
            file_path: Path to the source file

        Returns:
            List of CodeSymbol objects

        Example:
            >>> symbols = parser.parse_file("auth.py")
            >>> for sym in symbols:
            ...     print(f"{sym.symbol_type}: {sym.name}")
        """
        path = Path(file_path)
        if not path.exists():
            return []

        language = self._detect_language(file_path)

        if language == "python":
            return self._parse_python_file(file_path)
        else:
            # TODO: Add tree-sitter support for other languages
            return []

    def _parse_python_file(self, file_path: str) -> list[CodeSymbol]:
        """Parse Python file using AST."""
        symbols = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            lines = source.split("\n")

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    symbol = self._extract_function(node, lines, file_path, source)
                    if symbol:
                        symbols.append(symbol)

                elif isinstance(node, ast.ClassDef):
                    # Extract class
                    class_symbol = self._extract_class(node, lines, file_path, source)
                    if class_symbol:
                        symbols.append(class_symbol)

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method = self._extract_method(item, node, lines, file_path, source)
                            if method:
                                symbols.append(method)

        except SyntaxError as e:
            # Log error but return what we have
            print(f"Warning: Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")

        return symbols

    def _extract_function(
        self, node: ast.FunctionDef, lines: list[str], file_path: str, source: str
    ) -> CodeSymbol | None:
        """Extract function information from AST node."""
        try:
            start_line = node.lineno
            end_line = node.end_lineno or start_line

            # Get function content
            content = "\n".join(lines[start_line - 1 : end_line])

            # Build signature
            args = []
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)

            # Add *args and **kwargs
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")

            returns = ""
            if node.returns:
                returns = f" -> {ast.unparse(node.returns)}"

            signature = f"def {node.name}({', '.join(args)}){returns}:"

            # Extract docstring
            docstring = ast.get_docstring(node)

            # Get decorators
            decorators = []
            for decorator in node.decorator_list:
                try:
                    decorators.append(ast.unparse(decorator))
                except:
                    pass

            return CodeSymbol(
                name=node.name,
                symbol_type="function",
                content=content,
                signature=signature,
                docstring=docstring,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language="python",
                metadata={
                    "decorators": decorators,
                    "parameters": args,
                    "return_type": returns.replace(" -> ", "") if returns else None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                },
            )
        except Exception as e:
            print(f"Warning: Failed to extract function {getattr(node, 'name', '?')}: {e}")
            return None

    def _extract_class(
        self, node: ast.ClassDef, lines: list[str], file_path: str, source: str
    ) -> CodeSymbol | None:
        """Extract class information from AST node."""
        try:
            start_line = node.lineno
            end_line = node.end_lineno or start_line

            content = "\n".join(lines[start_line - 1 : end_line])

            # Build signature
            bases = [ast.unparse(base) for base in node.bases]
            bases_str = f"({', '.join(bases)})" if bases else ""
            signature = f"class {node.name}{bases_str}:"

            # Extract docstring
            docstring = ast.get_docstring(node)

            # Get decorators
            decorators = []
            for decorator in node.decorator_list:
                try:
                    decorators.append(ast.unparse(decorator))
                except:
                    pass

            return CodeSymbol(
                name=node.name,
                symbol_type="class",
                content=content,
                signature=signature,
                docstring=docstring,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language="python",
                metadata={
                    "decorators": decorators,
                    "bases": bases,
                    "method_count": sum(
                        1 for item in node.body if isinstance(item, ast.FunctionDef)
                    ),
                },
            )
        except Exception as e:
            print(f"Warning: Failed to extract class {getattr(node, 'name', '?')}: {e}")
            return None

    def _extract_method(
        self,
        node: ast.FunctionDef,
        class_node: ast.ClassDef,
        lines: list[str],
        file_path: str,
        source: str,
    ) -> CodeSymbol | None:
        """Extract method information from AST node."""
        try:
            start_line = node.lineno
            end_line = node.end_lineno or start_line

            content = "\n".join(lines[start_line - 1 : end_line])

            # Build signature (similar to function)
            args = []
            for i, arg in enumerate(node.args.args):
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)

            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")

            returns = ""
            if node.returns:
                returns = f" -> {ast.unparse(node.returns)}"

            signature = f"def {node.name}({', '.join(args)}){returns}:"

            docstring = ast.get_docstring(node)

            decorators = []
            for decorator in node.decorator_list:
                try:
                    decorators.append(ast.unparse(decorator))
                except:
                    pass

            return CodeSymbol(
                name=f"{class_node.name}.{node.name}",
                symbol_type="method",
                content=content,
                signature=signature,
                docstring=docstring,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language="python",
                metadata={
                    "class": class_node.name,
                    "decorators": decorators,
                    "parameters": args,
                    "return_type": returns.replace(" -> ", "") if returns else None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_property": any(d == "property" for d in decorators),
                },
            )
        except Exception as e:
            print(f"Warning: Failed to extract method {getattr(node, 'name', '?')}: {e}")
            return None

    def extract_imports(self, file_path: str) -> list[ImportInfo]:
        """Extract import statements from a file.

        Args:
            file_path: Path to the source file

        Returns:
            List of ImportInfo objects
        """
        imports = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            ImportInfo(
                                module=alias.name,
                                names=[alias.asname or alias.name],
                                is_from_import=False,
                                line=node.lineno,
                            )
                        )

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = [alias.name for alias in node.names]
                    imports.append(
                        ImportInfo(
                            module=module, names=names, is_from_import=True, line=node.lineno
                        )
                    )

        except Exception as e:
            print(f"Warning: Failed to extract imports from {file_path}: {e}")

        return imports

    def extract_function_calls(self, content: str) -> list[str]:
        """Extract function calls from code content.

        Args:
            content: Source code content

        Returns:
            List of function names called
        """
        calls = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Try to get function name
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.append(node.func.attr)

        except Exception:
            pass

        return calls


class CodeChunker:
    """Chunk code into embeddable pieces.

    Creates chunks that preserve context and are suitable for vector storage.

    Example:
        >>> chunker = CodeChunker()
        >>> chunks = chunker.chunk_file("auth.py")
        >>> for chunk in chunks:
        ...     print(f"{chunk.chunk_type}: {len(chunk.content)} chars")
    """

    def __init__(self, parser: CodeParser | None = None):
        self.parser = parser or CodeParser()

    def chunk_file(self, file_path: str) -> list[CodeChunk]:
        """Chunk a file into embeddable pieces.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeChunk objects
        """
        chunks = []

        # Parse symbols
        symbols = self.parser.parse_file(file_path)

        # Get imports for context
        imports = self.parser.extract_imports(file_path)
        import_context = self._format_imports(imports)

        # Create chunks for each symbol
        for symbol in symbols:
            if symbol.symbol_type in ("function", "method"):
                chunk = self._create_function_chunk(symbol, import_context)
                chunks.append(chunk)
            elif symbol.symbol_type == "class":
                chunk = self._create_class_chunk(symbol, import_context)
                chunks.append(chunk)

        return chunks

    def _format_imports(self, imports: list[ImportInfo]) -> str:
        """Format imports as context string."""
        lines = []
        for imp in imports:
            if imp.is_from_import:
                lines.append(f"from {imp.module} import {', '.join(imp.names)}")
            else:
                for name in imp.names:
                    lines.append(f"import {name}")
        return "\n".join(lines)

    def _create_function_chunk(self, symbol: CodeSymbol, import_context: str) -> CodeChunk:
        """Create a chunk for a function/method."""
        # Build rich content
        parts = []

        # Add signature
        parts.append(symbol.signature)

        # Add docstring if available
        if symbol.docstring:
            parts.append(f'"""{symbol.docstring}"""')

        # Add body (without docstring)
        body_lines = symbol.content.split("\n")[1:]  # Skip def line
        if body_lines and '"""' in body_lines[0] or "'''" in body_lines[0]:
            # Skip docstring lines
            i = 0
            while i < len(body_lines) and '"""' not in body_lines[i] and "'''" not in body_lines[i]:
                i += 1
            if i < len(body_lines):
                i += 1  # Skip closing docstring
            body_lines = body_lines[i:]

        parts.extend(body_lines)

        content = "\n".join(parts)

        # Build context
        context_parts = [f"# File: {symbol.file_path}"]
        if import_context:
            context_parts.append(f"# Imports:\n{import_context}")

        return CodeChunk(
            content=content,
            context="\n".join(context_parts),
            symbol=symbol,
            language=symbol.language,
            chunk_type="function",
        )

    def _create_class_chunk(self, symbol: CodeSymbol, import_context: str) -> CodeChunk:
        """Create a chunk for a class."""
        content = symbol.content

        # Build context
        context_parts = [f"# File: {symbol.file_path}"]
        if import_context:
            context_parts.append(f"# Imports:\n{import_context}")

        return CodeChunk(
            content=content,
            context="\n".join(context_parts),
            symbol=symbol,
            language=symbol.language,
            chunk_type="class",
        )


class CodeMemoryExtractor:
    """High-level extractor for indexing code into memory.

    Combines parsing and chunking to prepare code for vector storage.

    Example:
        >>> extractor = CodeMemoryExtractor()
        >>> chunks = extractor.extract_from_file("auth.py")
        >>> for chunk in chunks:
        ...     memory.add(chunk.content, source="auth.py", metadata={...})
    """

    def __init__(self):
        self.parser = CodeParser()
        self.chunker = CodeChunker(self.parser)

    def extract_from_file(self, file_path: str) -> list[CodeChunk]:
        """Extract chunks from a file ready for memory indexing.

        Args:
            file_path: Path to source file

        Returns:
            List of CodeChunk objects
        """
        return self.chunker.chunk_file(file_path)

    def extract_from_directory(
        self,
        dir_path: str,
        patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, list[CodeChunk]]:
        """Extract chunks from all files in a directory.

        Args:
            dir_path: Directory path
            patterns: File patterns to include (e.g., ["*.py"])
            exclude_patterns: Patterns to exclude

        Returns:
            Dictionary mapping file paths to chunks
        """
        patterns = patterns or ["*.py"]
        exclude_patterns = exclude_patterns or [
            "__pycache__/*",
            "*.pyc",
            ".git/*",
            ".venv/*",
            ".memnexus/*",
        ]

        results = {}
        dir_path = Path(dir_path)

        for pattern in patterns:
            for file_path in dir_path.rglob(pattern):
                # Check exclusions
                should_exclude = False
                for exclude in exclude_patterns:
                    if exclude in str(file_path):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                try:
                    chunks = self.extract_from_file(str(file_path))
                    if chunks:
                        results[str(file_path)] = chunks
                except Exception as e:
                    print(f"Warning: Failed to extract from {file_path}: {e}")

        return results

    def get_file_summary(self, file_path: str) -> dict[str, Any]:
        """Get a summary of a file's contents.

        Args:
            file_path: Path to source file

        Returns:
            Dictionary with summary information
        """
        symbols = self.parser.parse_file(file_path)
        imports = self.parser.extract_imports(file_path)

        functions = [s for s in symbols if s.symbol_type == "function"]
        classes = [s for s in symbols if s.symbol_type == "class"]
        methods = [s for s in symbols if s.symbol_type == "method"]

        return {
            "file_path": file_path,
            "language": self.parser._detect_language(file_path),
            "total_symbols": len(symbols),
            "functions": len(functions),
            "classes": len(classes),
            "methods": len(methods),
            "imports": len(imports),
            "function_names": [f.name for f in functions],
            "class_names": [c.name for c in classes],
        }
