"""git_diff_scanner — Git-aware file change detection for linting only modified files."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DiffResult:
    """Result of a git diff scan."""
    added: list[str]
    modified: list[str]
    deleted: list[str]
    renamed: list[tuple[str, str]]  # (old, new)

    @property
    def all_files(self) -> list[str]:
        """All changed files (added + modified + new names of renamed)."""
        files = list(self.added) + list(self.modified)
        files.extend(new for _, new in self.renamed)
        return files


def get_changed_files(
    base: str = "HEAD",
    target: str = "working",
    root: Optional[Path] = None,
) -> Optional[DiffResult]:
    """Get list of changed files between base and target.

    Args:
        base: Git ref to compare from (e.g. "HEAD", "main", "develop")
        target: Git ref to compare to ("working" for unstaged, "staged" for staged)
        root: Project root (defaults to current directory)

    Returns:
        DiffResult or None if not a git repo.
    """
    root = root or Path.cwd()

    # Check if we're in a git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=root,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    # Build diff command
    if target == "working":
        # Compare HEAD to working tree (unstaged + staged)
        cmd = ["git", "diff", "--name-status", base]
    elif target == "staged":
        # Compare staged changes
        cmd = ["git", "diff", "--name-status", "--cached"]
    else:
        # Compare two refs
        cmd = ["git", "diff", "--name-status", base, target]

    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        # If base ref doesn't exist, try without it
        try:
            cmd = ["git", "diff", "--name-status"]
            result = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return DiffResult(added=[], modified=[], deleted=[], renamed=[])

    added = []
    modified = []
    deleted = []
    renamed = []

    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status == "A":
            added.append(parts[1])
        elif status == "M":
            modified.append(parts[1])
        elif status == "D":
            deleted.append(parts[1])
        elif status.startswith("R"):
            # R100 old_file\tnew_file
            renamed.append((parts[1], parts[2]))

    return DiffResult(
        added=added,
        modified=modified,
        deleted=deleted,
        renamed=renamed,
    )


def filter_by_extensions(files: list[str], extensions: tuple[str, ...] = (".py", ".js", ".ts", ".jsx", ".tsx")) -> list[str]:
    """Filter files by allowed extensions."""
    return [f for f in files if any(f.endswith(ext) for ext in extensions)]


def get_changed_files_filtered(
    base: str = "HEAD",
    root: Optional[Path] = None,
    extensions: tuple[str, ...] = (".py", ".js", ".ts", ".jsx", ".tsx"),
) -> list[str]:
    """Get changed files filtered by extensions."""
    diff = get_changed_files(base=base, root=root)
    if diff is None:
        return []
    return filter_by_extensions(diff.all_files, extensions)
