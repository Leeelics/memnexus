"""Git history adapter for real repository evaluation."""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import logging

try:
    from adapters.base import BaseAdapter
    from core.base import StandardSample, StandardQA, QuestionCategory
except ImportError:
    from .base import BaseAdapter
    from ..core.base import StandardSample, StandardQA, QuestionCategory


class GitAdapter(BaseAdapter):
    """Adapter for Git repository-based benchmark datasets."""

    def __init__(
        self, repo_path: str, max_commits: int = 100, min_message_length: int = 20, logger=None
    ):
        super().__init__(repo_path, logger)
        self.repo_path = Path(repo_path)
        self.max_commits = max_commits
        self.min_message_length = min_message_length
        self._commits: List[Dict[str, Any]] = []

    def validate(self) -> bool:
        if not super().validate():
            return False
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self.logger.error(f"Not a git repository: {self.repo_path}")
            return False
        return True

    def _run_git_command(self, args: List[str]) -> str:
        cmd = ["git", "-C", str(self.repo_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            self.logger.warning(f"Git command failed: {' '.join(args)}")
            return ""
        return result.stdout

    def _extract_commits(self) -> List[Dict[str, Any]]:
        log_format = "%H|%ai|%an|%s"
        output = self._run_git_command(
            ["log", f"--format={log_format}", "-n", str(self.max_commits)]
        )

        commits = []
        for line in output.strip().split("\n"):
            if "|" not in line:
                continue
            parts = line.split("|", 3)
            if len(parts) != 4:
                continue

            commit_hash, date_str, author, message = parts
            if len(message) < self.min_message_length:
                continue
            if message.startswith("Merge"):
                continue

            commits.append(
                {
                    "hash": commit_hash[:8],
                    "full_hash": commit_hash,
                    "date": date_str,
                    "author": author,
                    "message": message,
                }
            )
        return commits

    def _generate_qa_from_commit(self, commit: Dict[str, Any]) -> List[StandardQA]:
        qa_pairs = []
        message = commit["message"]

        qa_pairs.append(
            StandardQA(
                question=f"What was changed in commit {commit['hash']}?",
                gold_answers=[message],
                evidence=[commit["hash"]],
                category=QuestionCategory.CHANGE_HISTORY,
                metadata={
                    "commit_hash": commit["hash"],
                    "author": commit["author"],
                    "date": commit["date"],
                    "type": "change_summary",
                },
            )
        )

        qa_pairs.append(
            StandardQA(
                question=f"Who made the change: '{message[:50]}...'?",
                gold_answers=[commit["author"]],
                evidence=[commit["hash"]],
                category=QuestionCategory.WHO_CHANGED,
                metadata={"commit_hash": commit["hash"], "type": "author_identification"},
            )
        )

        return qa_pairs

    def load_and_transform(self) -> List[StandardSample]:
        if not self.validate():
            return []

        self.logger.info(f"Extracting commits from {self.repo_path}")
        self._commits = self._extract_commits()
        self.logger.info(f"Found {len(self._commits)} commits")

        samples = []
        for commit in self._commits:
            qa_pairs = self._generate_qa_from_commit(commit)
            if qa_pairs:
                sample = StandardSample(
                    sample_id=commit["hash"],
                    qa_pairs=qa_pairs,
                    context=commit["message"],
                    metadata={
                        "author": commit["author"],
                        "date": commit["date"],
                        "repo": str(self.repo_path),
                    },
                )
                samples.append(sample)

        self.logger.info(f"Generated {len(samples)} samples")
        return samples

    def get_expected_evidence(self, qa: StandardQA) -> List[str]:
        return qa.metadata.get("commit_hash", [])

    def export_to_json(self, output_path: str) -> None:
        samples = self.load_and_transform()
        data = {
            "metadata": {
                "source": "git_history",
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
