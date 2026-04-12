from capabilities.linting_analysis_actions import RunAnalysisUseCase, ApplyFixesUseCase
from capabilities.hooks_management_actions import HookManagementUseCase
from capabilities.linting_governance_adapter import GovernanceAdapter
from infrastructure.python_linter_adapters import (
    RuffAdapter,
    MyPyAdapter,
    BanditAdapter,
    ComplexityAdapter,
    DependencyAdapter,
    DuplicateAdapter,
    TrendsAdapter,
)
from infrastructure.javascript_linter_adapter import (
    PrettierAdapter,
    TSCAdapter,
    ESLintAdapter,
)
from infrastructure.python_ast_tracer import PythonTracer
from infrastructure.javascript_call_tracer import JSTracer
from infrastructure.git_hooks_manager import GitHookManager
import os
import sys
from typing import List
from taxonomy.lint_result_models import ILinterAdapter


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
        self.adapters: List[ILinterAdapter] = [
            RuffAdapter(bin_path=vbin),
            MyPyAdapter(bin_path=vbin),
            BanditAdapter(bin_path=vbin),
            ComplexityAdapter(bin_path=vbin),
            DependencyAdapter(bin_path=vbin),
            DuplicateAdapter(bin_path=vbin),
            TrendsAdapter(),
            PrettierAdapter(),
            TSCAdapter(),
            ESLintAdapter(),
            GovernanceAdapter(tracer=self.python_tracer),
        ]

        # Use cases
        self.analysis_use_case = RunAnalysisUseCase(self.adapters, tracers=self.tracers)
        self.fixes_use_case = ApplyFixesUseCase(self.adapters, tracers=self.tracers)
        self.hook_manager = GitHookManager(root_dir=os.getcwd())
        self.hooks_use_case = HookManagementUseCase(self.hook_manager)



_container = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container
