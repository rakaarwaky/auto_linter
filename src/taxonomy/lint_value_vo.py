"""lint_value_vo — Core linting value objects."""

from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator


class Severity(str, Enum):
    """Lint finding impact level."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def score_impact(self) -> float:
        return _SEVERITY_IMPACT[self]


_SEVERITY_IMPACT = {
    Severity.INFO: 0,
    Severity.LOW: 0,
    Severity.MEDIUM: 2,
    Severity.HIGH: 10,
    Severity.CRITICAL: 50,
}


class ErrorCode(BaseModel):
    """Linter error code."""
    model_config = ConfigDict(frozen=True)

    code: str

    def __str__(self) -> str:
        return self.code

    @property
    def is_style(self) -> bool:
        return self.code.startswith(("E", "W", "D"))

    @property
    def is_logic(self) -> bool:
        return self.code.startswith(("F", "I"))

    @property
    def is_security(self) -> bool:
        return self.code.startswith("B")

    @property
    def is_governance(self) -> bool:
        return self.code.startswith("AES")


class Position(BaseModel):
    """Source file location."""
    model_config = ConfigDict(frozen=True)

    line: int
    column: int = 0

    def __str__(self) -> str:
        if self.column:
            return f"{self.line}:{self.column}"
        return str(self.line)


class Score(BaseModel):
    """Governance score (0.0-100.0)."""
    model_config = ConfigDict(frozen=True)

    value: float

    @field_validator("value")
    @classmethod
    def check_range(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"Score must be 0.0-100.0, got {v}")
        return v

    def __str__(self) -> str:
        return f"{self.value:.1f}"

    @property
    def is_passing(self) -> bool:
        return self.value >= 80.0

    @property
    def is_perfect(self) -> bool:
        return self.value >= 100.0

    def deduct(self, severity: Severity) -> "Score":
        new_val = max(0.0, self.value - severity.score_impact)
        return Score(value=new_val)


class FileFormat(BaseModel):
    """Report output format."""
    model_config = ConfigDict(frozen=True)

    name: str

    def __str__(self) -> str:
        return self.name

    @property
    def is_structured(self) -> bool:
        return self.name in ("json", "sarif", "junit")


# Common format constants
FORMAT_TEXT = FileFormat(name="text")
FORMAT_JSON = FileFormat(name="json")
FORMAT_SARIF = FileFormat(name="sarif")
FORMAT_JUNIT = FileFormat(name="junit")

ALL_FORMATS = (FORMAT_TEXT, FORMAT_JSON, FORMAT_SARIF, FORMAT_JUNIT)
