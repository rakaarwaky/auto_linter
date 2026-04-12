"""lint_identifier_vo — Identifier value objects for linting."""

from pydantic import BaseModel, ConfigDict, field_validator


class AdapterName(BaseModel):
    """Adapter/tool identifier."""
    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Adapter name cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AdapterName):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented


class FilePath(BaseModel):
    """File path identifier."""
    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip().replace("\\", "/").rstrip("/")

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FilePath):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    @property
    def extension(self) -> str:
        """File extension without dot."""
        # Special filenames without extension (Makefile, Dockerfile, etc.)
        special_files = {"Makefile", "Dockerfile", "Dockerfile.dev", "Dockerfile.prod",
                         ".bashrc", ".profile", ".zshrc", ".gitignore", ".dockerignore"}
        if self.value in special_files or self.value.startswith("."):
            return ""
        parts = self.value.rsplit(".", 1)
        return parts[-1] if len(parts) > 1 else ""

    def has_extension(self, ext: str) -> bool:
        """Check if path has given extension (without dot)."""
        return self.extension.lower() == ext.lower()


class SymbolName(BaseModel):
    """Code symbol identifier (function, class, variable)."""
    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def check_valid_symbol(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Symbol name cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SymbolName):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented


class DirectoryPath(BaseModel):
    """Directory path identifier."""
    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Directory path cannot be empty")
        return v.strip().replace("\\", "/").rstrip("/")

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DirectoryPath):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented
