"""lint_scan_event — Linting domain event types."""

from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict

from taxonomy.lint_value_vo import Severity, ErrorCode, Score
from taxonomy.lint_identifier_vo import FilePath, AdapterName


class ScanStarted(BaseModel):
    """Scan began."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    adapters: List[AdapterName]
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class ScanCompleted(BaseModel):
    """Scan finished."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    score: Score
    worst_severity: Severity
    violation_count: int
    duration_ms: float
    timestamp: str = ""

    @property
    def is_passing(self) -> bool:
        return self.score.is_passing

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class ScanFailed(BaseModel):
    """Scan failed."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    adapter: AdapterName
    error_message: str
    error_code: Optional[ErrorCode] = None
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class FixApplied(BaseModel):
    """Fix applied to a file."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    adapter: AdapterName
    error_code: ErrorCode
    changes_count: int
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class AdapterRegistered(BaseModel):
    """Adapter loaded."""
    model_config = ConfigDict(frozen=True)

    adapter_name: AdapterName
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class HookInstalled(BaseModel):
    """Pre-commit hook installed."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    executable: FilePath
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class HookRemoved(BaseModel):
    """Pre-commit hook removed."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())
