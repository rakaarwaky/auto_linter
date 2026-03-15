from src.core.capabilities.linting.actions import RunAnalysisUseCase, ApplyFixesUseCase
from src.core.capabilities.linting.governance import GovernanceAdapter
from src.infrastructure.adapters import (
    RuffAdapter,
    MyPyAdapter,
    PrettierAdapter,
    TSCAdapter,
    ESLintAdapter,
    PythonTracer,
    JSTracer,
)
import os
import sys


class Container:
    """Dependency Injection container (Bootstrap)."""

    def __init__(self):
        # Tracers (Infrastructure)
        self.python_tracer = PythonTracer()
        self.js_tracer = JSTracer()
        self.tracers = {
            "python": self.python_tracer,
            "js": self.js_tracer
        }

        # Discover and register adapters
        vbin = os.path.dirname(sys.executable)
        self.venv_bin = vbin
        self.adapters = [
            RuffAdapter(bin_path=vbin),
            MyPyAdapter(bin_path=vbin),
            PrettierAdapter(),
            TSCAdapter(),
            ESLintAdapter(),
            GovernanceAdapter(tracer=self.python_tracer),
        ]

        # Use cases
        self.analysis_use_case = RunAnalysisUseCase(self.adapters, tracers=self.tracers)
        self.fixes_use_case = ApplyFixesUseCase(self.venv_bin, tracers=self.tracers)


_container = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container
