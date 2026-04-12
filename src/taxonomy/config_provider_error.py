"""config_provider_error — Configuration domain error types."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

from taxonomy.config_identifier_vo import ConfigKey
from taxonomy.lint_identifier_vo import FilePath


class ConfigError(BaseModel):
    """Invalid or missing configuration."""
    model_config = ConfigDict(frozen=True)

    key: ConfigKey
    message: str
    expected: str = ""
    actual: str = ""
    config_file: Optional[FilePath] = None

    def __str__(self) -> str:
        file_info = f" in {self.config_file}" if self.config_file else ""
        return f"Config error on '{self.key}'{file_info}: {self.message}"
