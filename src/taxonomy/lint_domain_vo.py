"""lint_domain_vo — Domain value objects: scope, location, constraint, command."""

from pydantic import BaseModel, ConfigDict, field_validator


class ScopeRef(BaseModel):
    """Code scope reference (function, class, module)."""
    model_config = ConfigDict(frozen=True)

    name: str
    kind: str = "function"
    file: str = ""
    start_line: int = 0
    end_line: int = 0

    @field_validator("name")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Scope name cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        if self.file:
            prefix = f"{self.kind} " if self.kind else ""
            return f"{prefix}{self.name} in {self.file}"
        if self.kind:
            return f"{self.kind} {self.name}"
        return self.name

    @property
    def has_range(self) -> bool:
        return self.start_line > 0 and self.end_line > 0


class Location(BaseModel):
    """File location with optional description."""
    model_config = ConfigDict(frozen=True)

    file: str = ""
    line: int = 0
    column: int = 0
    description: str = ""

    def __str__(self) -> str:
        parts = []
        if self.file:
            parts.append(self.file)
        if self.line:
            parts.append(str(self.line))
            if self.column:
                parts[-1] += f":{self.column}"
        result = ":".join(parts) if parts else "unknown"
        if self.description:
            result += f" — {self.description}"
        return result


class ViolationConstraint(BaseModel):
    """Validation constraint descriptor."""
    model_config = ConfigDict(frozen=True)

    rule: str
    min_value: str = ""
    max_value: str = ""

    def __str__(self) -> str:
        parts = [self.rule]
        if self.min_value or self.max_value:
            range_str = f"{self.min_value}..{self.max_value}" if self.min_value and self.max_value else (self.min_value or self.max_value)
            parts.append(f"(must be {range_str})")
        return " ".join(parts)


class CommandArgs(BaseModel):
    """Command line arguments list."""
    model_config = ConfigDict(frozen=True)

    args: list[str] = []

    def __str__(self) -> str:
        return " ".join(self.args)

    def __len__(self) -> int:
        return len(self.args)
