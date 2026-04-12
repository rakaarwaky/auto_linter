"""Re-exports for backward compatibility after splitting python.py."""
from infrastructure.python_ruff_adapter import RuffAdapter
from infrastructure.python_mypy_adapter import MyPyAdapter
from infrastructure.python_bandit_adapter import BanditAdapter
from infrastructure.python_analysis_adapters import (
    ComplexityAdapter,
    DuplicateAdapter,
    TrendsAdapter,
    DependencyAdapter,
)

__all__ = [
    "RuffAdapter",
    "MyPyAdapter",
    "BanditAdapter",
    "ComplexityAdapter",
    "DuplicateAdapter",
    "TrendsAdapter",
    "DependencyAdapter",
]
