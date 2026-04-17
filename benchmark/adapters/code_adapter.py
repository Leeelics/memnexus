"""Code repository adapter for code retrieval evaluation."""

import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    from adapters.base import BaseAdapter
    from core.base import StandardSample, StandardQA, QuestionCategory
except ImportError:
    from .base import BaseAdapter
    from ..core.base import StandardSample, StandardQA, QuestionCategory


class CodeAdapter(BaseAdapter):
    """Adapter for code repository-based benchmark datasets."""

    def __init__(self, repo_path: str, file_pattern: str = "*.py", logger=None):
        super().__init__(repo_path, logger)
        self.repo_path = Path(repo_path)
        self.file_pattern = file_pattern
        self._symbols: List[Dict[str, Any]] = []

    def _find_python_files(self) -> List[Path]:
        files = []
        for py_file in self.repo_path.rglob(self.file_pattern):
            if any(part.startswith(".") for part in py_file.relative_to(self.repo_path).parts):
                continue
            if "test" in py_file.name.lower() and py_file.name != "test":
                continue
            files.append(py_file)
        return files[:50]

    def _extract_symbols(self, file_path: Path) -> List[Dict[str, Any]]:
        symbols = []
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node) or ""
                    symbols.append(
                        {
                            "type": "function",
                            "name": node.name,
                            "file": str(file_path.relative_to(self.repo_path)),
                            "line": node.lineno,
                            "docstring": docstring[:200] if docstring else "",
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    symbols.append(
                        {
                            "type": "class",
                            "name": node.name,
                            "file": str(file_path.relative_to(self.repo_path)),
                            "line": node.lineno,
                            "docstring": docstring[:200] if docstring else "",
                        }
                    )
        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {e}")
        return symbols

    def _generate_qa_from_symbol(self, symbol: Dict[str, Any]) -> List[StandardQA]:
        qa_pairs = []

        if symbol["docstring"]:
            qa_pairs.append(
                StandardQA(
                    question=f"What does the {symbol['type']} '{symbol['name']}' do?",
                    gold_answers=[symbol["docstring"]],
                    evidence=[f"{symbol['file']}:{symbol['line']}"],
                    category=QuestionCategory.FUNCTION_PURPOSE,
                    metadata={
                        "symbol_name": symbol["name"],
                        "symbol_type": symbol["type"],
                        "file": symbol["file"],
                        "line": symbol["line"],
                    },
                )
            )

        qa_pairs.append(
            StandardQA(
                question=f"Where is the {symbol['type']} '{symbol['name']}' defined?",
                gold_answers=[f"{symbol['file']}:{symbol['line']}"],
                evidence=[f"{symbol['file']}:{symbol['line']}"],
                category=QuestionCategory.FIND_DEFINITION,
                metadata={
                    "symbol_name": symbol["name"],
                    "symbol_type": symbol["type"],
                    "file": symbol["file"],
                    "line": symbol["line"],
                },
            )
        )

        return qa_pairs

    def load_and_transform(self) -> List[StandardSample]:
        self.logger.info(f"Scanning Python files in {self.repo_path}")
        py_files = self._find_python_files()
        self.logger.info(f"Found {len(py_files)} Python files")

        all_symbols = []
        for py_file in py_files:
            symbols = self._extract_symbols(py_file)
            all_symbols.extend(symbols)

        self.logger.info(f"Extracted {len(all_symbols)} symbols")

        samples = []
        file_symbols: Dict[str, List[Dict]] = {}
        for symbol in all_symbols:
            file_path = symbol["file"]
            if file_path not in file_symbols:
                file_symbols[file_path] = []
            file_symbols[file_path].append(symbol)

        for file_path, symbols in file_symbols.items():
            qa_pairs = []
            for symbol in symbols:
                qa_pairs.extend(self._generate_qa_from_symbol(symbol))

            if qa_pairs:
                sample = StandardSample(
                    sample_id=file_path,
                    qa_pairs=qa_pairs,
                    context=f"File: {file_path}",
                    metadata={"file": file_path, "num_symbols": len(symbols)},
                )
                samples.append(sample)

        self.logger.info(f"Generated {len(samples)} samples")
        return samples

    def get_expected_evidence(self, qa: StandardQA) -> List[str]:
        return qa.evidence

    def export_to_json(self, output_path: str) -> None:
        samples = self.load_and_transform()
        data = {
            "metadata": {
                "source": "code_repository",
                "repo_path": str(self.repo_path),
                "generated_at": datetime.now().isoformat(),
                "num_samples": len(samples),
                "num_qa_pairs": sum(len(s.qa_pairs) for s in samples),
            },
            "samples": [
                {
                    "sample_id": s.sample_id,
                    "context": s.context,
                    "qa_pairs": [
                        {
                            "question": qa.question,
                            "gold_answers": qa.gold_answers,
                            "evidence": qa.evidence,
                            "category": qa.category,
                            "metadata": qa.metadata,
                        }
                        for qa in s.qa_pairs
                    ],
                }
                for s in samples
            ],
        }
        Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        self.logger.info(f"Exported to {output_path}")
