"""taxonomy — Shared language for all domains (VOs, entities, errors, events)."""

__all__ = [
    # Value Objects: Core
    "Severity", "ErrorCode", "Position", "Score", "FileFormat",
    "FORMAT_TEXT", "FORMAT_JSON", "FORMAT_SARIF", "FORMAT_JUNIT", "ALL_FORMATS",
    # Value Objects: Identifiers
    "AdapterName", "FilePath", "SymbolName", "DirectoryPath",
    # Value Objects: Domain
    "ScopeRef", "Location", "CommandArgs",
    # Value Objects: Transport
    "TransportProtocol", "TransportEndpoint",
    # Value Objects: Config
    "Thresholds", "AdapterStatus", "AdapterEntry", "ProjectConfig",
    "DEFAULT_THRESHOLDS", "ConfigKey",
    # Entities
    "LintResult", "GovernanceReport", "ILinterAdapter", "ISemanticTracer", "IHookManager",
    # Errors
    "AdapterError", "ScanError", "ValidationError",
    "TransportError",
    "ConfigError",
    # Events
    "ScanStarted", "ScanCompleted", "ScanFailed", "FixApplied",
    "AdapterRegistered", "HookInstalled", "HookRemoved",
]

# -- Value Objects: Core --
from taxonomy.lint_value_vo import (
    Severity as Severity,
    ErrorCode as ErrorCode,
    Position as Position,
    Score as Score,
    FileFormat as FileFormat,
    FORMAT_TEXT as FORMAT_TEXT,
    FORMAT_JSON as FORMAT_JSON,
    FORMAT_SARIF as FORMAT_SARIF,
    FORMAT_JUNIT as FORMAT_JUNIT,
    ALL_FORMATS as ALL_FORMATS,
)

# -- Value Objects: Identifiers --
from taxonomy.lint_identifier_vo import (
    AdapterName as AdapterName,
    FilePath as FilePath,
    SymbolName as SymbolName,
    DirectoryPath as DirectoryPath,
)

# -- Value Objects: Domain --
from taxonomy.lint_domain_vo import (
    ScopeRef as ScopeRef,
    Location as Location,
    CommandArgs as CommandArgs,
)

# -- Value Objects: Transport --
from taxonomy.transport_protocol_vo import (
    TransportProtocol as TransportProtocol,
    TransportEndpoint as TransportEndpoint,
)

# -- Value Objects: Config --
from taxonomy.config_setting_vo import (
    Thresholds as Thresholds,
    AdapterStatus as AdapterStatus,
    AdapterEntry as AdapterEntry,
    ProjectConfig as ProjectConfig,
    DEFAULT_THRESHOLDS as DEFAULT_THRESHOLDS,
)

from taxonomy.config_identifier_vo import (
    ConfigKey as ConfigKey,
)

# -- Entities --
from taxonomy.lint_result_entity import (
    LintResult as LintResult,
    GovernanceReport as GovernanceReport,
    ILinterAdapter as ILinterAdapter,
    ISemanticTracer as ISemanticTracer,
    IHookManager as IHookManager,
)

# -- Errors --
from taxonomy.lint_adapter_error import (
    AdapterError as AdapterError,
    ScanError as ScanError,
    ValidationError as ValidationError,
)

from taxonomy.transport_client_error import (
    TransportError as TransportError,
)

from taxonomy.config_provider_error import (
    ConfigError as ConfigError,
)

# -- Events --
from taxonomy.lint_scan_event import (
    ScanStarted as ScanStarted,
    ScanCompleted as ScanCompleted,
    ScanFailed as ScanFailed,
    FixApplied as FixApplied,
    AdapterRegistered as AdapterRegistered,
    HookInstalled as HookInstalled,
    HookRemoved as HookRemoved,
)
