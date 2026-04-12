"""Infrastructure layer - re-exports all public adapters."""

from infrastructure.python_ruff_adapter import RuffAdapter
from infrastructure.python_mypy_adapter import MyPyAdapter
from infrastructure.python_bandit_adapter import BanditAdapter
from infrastructure.python_analysis_adapters import (
    ComplexityAdapter,
    DuplicateAdapter,
    TrendsAdapter,
    DependencyAdapter,
)
from infrastructure.python_ast_tracer import PythonTracer
from infrastructure.javascript_linter_adapter import (
    PrettierAdapter,
    TSCAdapter,
    ESLintAdapter,
)
from infrastructure.javascript_call_tracer import JSTracer
from infrastructure.desktop_commander_adapter import (
    DesktopCommanderAdapter,
    detect_protocol,
    execute_via_desktop_commander,
)
from infrastructure.http_request_client import HTTPClient
from infrastructure.unix_socket_client import UnixSocketClient
from infrastructure.git_hooks_manager import GitHookManager

__all__ = [
    "RuffAdapter",
    "MyPyAdapter",
    "BanditAdapter",
    "ComplexityAdapter",
    "DuplicateAdapter",
    "TrendsAdapter",
    "DependencyAdapter",
    "PythonTracer",
    "PrettierAdapter",
    "TSCAdapter",
    "ESLintAdapter",
    "JSTracer",
    "DesktopCommanderAdapter",
    "detect_protocol",
    "execute_via_desktop_commander",
    "HTTPClient",
    "UnixSocketClient",
    "GitHookManager",
]
