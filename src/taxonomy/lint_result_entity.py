"""lint_result_entity — Linting domain entities and interfaces."""

from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod

from taxonomy.lint_value_vo import Severity, ErrorCode, Position, Score
from taxonomy.lint_identifier_vo import FilePath, AdapterName, SymbolName, DirectoryPath
from taxonomy.lint_domain_vo import ScopeRef, Location


@dataclass
class LintResult:
    """A single lint finding."""
    file: FilePath
    line: int
    column: int = 0
    code: str = ""
    message: str = ""
    source: AdapterName | str | None = None
    severity: Severity = Severity.MEDIUM
    enclosing_scope: Optional[ScopeRef] = None
    related_locations: List[Location | str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.file, str):
            object.__setattr__(self, "file", FilePath(value=self.file))
        if isinstance(self.source, str):
            object.__setattr__(self, "source", AdapterName(value=self.source))
        normalized: List[Location] = []
        for item in self.related_locations:
            if isinstance(item, str):
                normalized.append(Location(description=item))
            else:
                normalized.append(item)
        object.__setattr__(self, "related_locations", normalized)

    @property
    def position(self) -> Position:
        return Position(line=self.line, column=self.column)

    @property
    def error_code(self) -> ErrorCode:
        return ErrorCode(code=self.code)

    @property
    def identity(self) -> str:
        """Unique key for deduplication."""
        return f"{self.file}:{self.line}:{self.code}:{self.source}"

    def enrich(self, enclosing_scope: Optional[ScopeRef] = None, related: Optional[List[Location]] = None):
        """Add contextual information from semantic analysis."""
        if enclosing_scope:
            object.__setattr__(self, "enclosing_scope", enclosing_scope)
        if related:
            self.related_locations.extend(related)


@dataclass
class GovernanceReport:
    """Aggregated lint scan results."""
    results: List[LintResult] = field(default_factory=list)
    score: float = 100.0
    is_passing: bool = True

    def add_result(self, result: LintResult):
        """Add a finding and update score."""
        self.results.append(result)
        new_score = Score(value=max(0.0, self.score - result.severity.score_impact))
        self.score = new_score.value
        if result.severity == Severity.CRITICAL or self.score < 80.0:
            self.is_passing = False

    def results_by_source(self, source: str) -> List[LintResult]:
        """Filter results by adapter source."""
        return [r for r in self.results if str(r.source or "") == source]

    @property
    def violation_count(self) -> int:
        return len([r for r in self.results if r.severity.score_impact > 0])

    @property
    def sources(self) -> List[str]:
        """Unique adapter sources that produced results."""
        return list(dict.fromkeys(str(r.source) for r in self.results if r.source))


class ILinterAdapter(ABC):
    """Interface for external linting tools."""

    @abstractmethod
    def scan(self, path: FilePath | str) -> List[LintResult]:
        ...

    @abstractmethod
    def apply_fix(self, path: FilePath | str) -> bool:
        ...

    @abstractmethod
    def name(self) -> str:
        ...


class ISemanticTracer(ABC):
    """Interface for semantic analysis."""

    @abstractmethod
    def show_enclosing_scope(self, file_path: FilePath | str, line: int) -> Optional[ScopeRef]:
        ...

    @abstractmethod
    def trace_call_chain(self, root_dir: DirectoryPath | str, target_name: SymbolName | str) -> List[str]:
        ...

    @abstractmethod
    def find_flow(self, file_path: FilePath | str, var_name: SymbolName | str, start_line: int) -> List[str]:
        ...

    @abstractmethod
    def get_variant_dict(self, name: SymbolName | str) -> dict:
        ...

    @abstractmethod
    def project_wide_rename(self, root_dir: DirectoryPath | str, old_name: SymbolName | str, new_name: SymbolName | str) -> int:
        ...


class IHookManager(ABC):
    """Interface for Git hook management."""

    @abstractmethod
    def install_pre_commit(self, executable_path: FilePath | str = "auto-lint") -> bool:
        ...

    @abstractmethod
    def uninstall_pre_commit(self) -> bool:
        ...
