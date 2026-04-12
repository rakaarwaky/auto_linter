from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"

@dataclass
class LintResult:
    """Core entity representing a single linting finding (Taxonomy)."""
    file: str
    line: int
    column: Optional[int]
    code: str
    message: str
    source: str
    severity: Severity = Severity.MEDIUM
    enclosing_scope: Optional[str] = None
    related_locations: List[str] = field(default_factory=list)

@dataclass
class GovernanceReport:
    """Aggregated results and score of a linting session (Taxonomy)."""
    results: List[LintResult] = field(default_factory=list)
    score: float = 100.0
    is_passing: bool = True

    def add_result(self, result: LintResult):
        self.results.append(result)
        
        if result.severity == Severity.CRITICAL:
            self.score -= 50
            self.is_passing = False
        elif result.severity == Severity.HIGH:
            self.score -= 10
        elif result.severity == Severity.MEDIUM:
            self.score -= 2
        
        self.score = max(0.0, self.score)

class ILinterAdapter(ABC):
    """Interface for external linting tools (Taxonomy)."""
    
    @abstractmethod
    def scan(self, path: str) -> List[LintResult]:
        """Scans the given path and returns a list of standardized results."""
        ...

    @abstractmethod
    def apply_fix(self, path: str) -> bool:
        """Applies automatic fixes to the given path. Returns True if successful."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Returns the name of the tool (e.g., 'ruff')."""
        ...

class ISemanticTracer(ABC):
    """Interface for tracing and refactoring capabilities (Taxonomy)."""
    
    @abstractmethod
    def show_enclosing_scope(self, file_path: str, line: int) -> Optional[str]:
        """Returns the name of the function or class enclosing the given line."""
        ...
        
    @abstractmethod
    def trace_call_chain(self, root_dir: str, target_name: str) -> List[str]:
        """Finds all call sites for the target name within the project."""
        ...
        
    @abstractmethod
    def find_flow(self, file_path: str, var_name: str, start_line: int) -> List[str]:
        """Tracks the lifecycle of a variable within a file."""
        ...
        
    @abstractmethod
    def get_variant_dict(self, name: str) -> dict:
        """Returns naming variants (camelCase, snake_case, etc) for a name."""
        ...
        
    @abstractmethod
    def project_wide_rename(self, root_dir: str, old_name: str, new_name: str) -> int:
        """Renames a symbol across all files in the project."""
        ...

class IHookManager(ABC):
    """Interface for Git hook management (Taxonomy)."""
    
    @abstractmethod
    def install_pre_commit(self, executable_path: str = "auto-lint") -> bool:
        """Installs the pre-commit hook."""
        ...

    @abstractmethod
    def uninstall_pre_commit(self) -> bool:
        """Uninstalls the pre-commit hook."""
        ...
