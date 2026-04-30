from capabilities.linting_analysis_actions import RunAnalysisUseCase, ApplyFixesUseCase
from capabilities.hooks_management_actions import HookManagementUseCase
from capabilities.linting_governance_adapter import GovernanceAdapter
from capabilities.semantic_scope_analyzer import SemanticScopeAnalyzer
from capabilities.call_chain_analyzer import CallChainAnalyzer
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
from infrastructure.git_diff_scanner import get_changed_files, filter_by_extensions
from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter
from infrastructure.plugin_system import discover_plugins, list_custom_adapters
from infrastructure.config_validation_provider import get_config
from agent.lifecycle_state_manager import get_state
from agent.pipeline_execution_orchestrator import Pipeline
from agent.multi_project_orchestrator import MultiProjectOrchestrator
import os
import sys
from typing import List, Tuple
from taxonomy.lint_result_models import ILinterAdapter


class Container:
    """Dependency Injection container (Bootstrap).

    Agent responsibilities:
    - Lifecycle: track agent state (started, stopped, degraded, uptime)
    - Pipeline: receive -> think -> act -> respond orchestration
    - Wiring: assemble adapters, use cases, tracers, analyzers
    """

    def __init__(self):
        config = get_config()

        # Convert List[Dict] to List[Tuple] for GovernanceAdapter
        rules: List[Tuple[str, str, str]] = []
        for r in config.project.governance_rules:
            if isinstance(r, dict):
                rules.append((
                    r.get('from', ''),
                    r.get('to', ''),
                    r.get('description', '')
                ))

        layer_map = config.project.layer_map or {
            "infrastructure": "infrastructure",
            "capabilities": "capabilities",
            "surfaces": "surfaces",
            "agent": "agent",
            "taxonomy": "taxonomy",
        }

        # === LIFECYCLE MANAGEMENT ===
        self.state_manager = get_state()
        self.state_manager.mark_started()

        # === TRACERS ===
        self.python_tracer = PythonTracer()
        self.js_tracer = JSTracer()
        self.tracers = {
            "python": self.python_tracer,
            "js": self.js_tracer
        }

        # === SEMANTIC ANALYZERS ===
        self.scope_analyzer = SemanticScopeAnalyzer()
        self.call_chain_analyzer = CallChainAnalyzer()
        self.semantic_analyzers = {
            "scope": self.scope_analyzer,
            "call_chain": self.call_chain_analyzer,
        }

        # === ADAPTERS ===
        vbin = os.path.dirname(sys.executable)
        self.venv_bin = vbin
        # click.echo(f"Wiring adapters with vbin: {vbin}")
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
            GovernanceAdapter(
                tracer=self.python_tracer,
                rules=rules if rules else None,
                layer_map=layer_map
            ),
        ]
        # click.echo(f"Initialized {len(self.adapters)} adapters.")

        # === USE CASES ===
        self.analysis_use_case = RunAnalysisUseCase(
            self.adapters, 
            tracers=self.tracers,
            threshold=config.thresholds.score
        )
        self.fixes_use_case = ApplyFixesUseCase(self.adapters, tracers=self.tracers)
        self.hook_manager = GitHookManager(root_dir=os.getcwd())
        self.hooks_use_case = HookManagementUseCase(self.hook_manager)

        # === PIPELINE (Brain Stem) ===
        self.pipeline = Pipeline(self)

        # === MULTI-PROJECT ORCHESTRATOR ===
        self.multi_project = MultiProjectOrchestrator(self.analysis_use_case)

        # === DESKTOP COMMANDER (External tool transport) ===
        self.desktop_commander = DesktopCommanderAdapter()

    # === GIT DIFF (Surface support) ===
    def get_git_diff(self, base: str = "HEAD") -> dict | None:
        """Get changed files — surface calls this, agent coordinates."""
        diff = get_changed_files(base=base)
        if diff is None:
            return None
        return {
            "added": diff.added,
            "modified": diff.modified,
            "deleted": diff.deleted,
            "renamed": [{"old": old, "new": new} for old, new in diff.renamed],
            "lintable_files": filter_by_extensions(diff.all_files),
            "all_files": diff.all_files,
            "total_changed": len(diff.all_files),
        }

    # === PLUGIN DISCOVERY (Surface support) ===
    def get_discovered_plugins(self) -> dict:
        """Return discovered plugins — surface calls this, agent coordinates."""
        return discover_plugins()

    def get_custom_adapters(self) -> list:
        """Return registered custom adapters — surface calls this, agent coordinates."""
        return list_custom_adapters()

    # === LIFECYCLE API ===
    def health(self) -> dict:
        """Return full health report: lifecycle + pipeline status."""
        return {
            "lifecycle": self.state_manager.health(),
            "adapters": [a.name() for a in self.adapters],
            "adapter_count": len(self.adapters),
        }

    def shutdown(self) -> None:
        """Graceful shutdown — mark lifecycle as stopped."""
        self.state_manager.mark_stopped()


_container = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset singleton — useful for testing."""
    global _container
    _container = None
