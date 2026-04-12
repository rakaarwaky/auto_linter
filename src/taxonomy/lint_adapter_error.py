"""lint_adapter_error — Linting domain error types."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

from taxonomy.lint_value_vo import ErrorCode
from taxonomy.lint_identifier_vo import FilePath, AdapterName
from taxonomy.lint_domain_vo import CommandArgs


class AdapterError(BaseModel):
    """External linter tool failed."""
    model_config = ConfigDict(frozen=True)

    adapter_name: AdapterName
    message: str
    error_code: Optional[ErrorCode] = None
    command: CommandArgs = CommandArgs()
    stderr: str = ""
    exit_code: Optional[int] = None

    def __str__(self) -> str:
        code = f" [{self.error_code}]" if self.error_code else ""
        return f"[{self.adapter_name}]{code} {self.message}"


class ScanError(BaseModel):
    """Scan operation failed on a path."""
    model_config = ConfigDict(frozen=True)

    path: FilePath
    message: str
    error_code: Optional[ErrorCode] = None
    adapter_name: Optional[AdapterName] = None
    cause: Optional[str] = None

    def __str__(self) -> str:
        adapter = f" ({self.adapter_name})" if self.adapter_name else ""
        code = f" [{self.error_code}]" if self.error_code else ""
        return f"Scan failed{adapter}{code}: {self.path} — {self.message}"


class ValidationError(BaseModel):
    """Input validation failed."""
    model_config = ConfigDict(frozen=True)

    field_name: str
    message: str
    constraint: str = ""
    value: str = ""

    def __str__(self) -> str:
        return f"Validation failed on '{self.field_name}': {self.message}"
