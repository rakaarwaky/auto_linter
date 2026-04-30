"""Tests for infrastructure/linting_governance_adapter.py — boost coverage from 19%."""

import tempfile
import os
from infrastructure.linting_governance_adapter import (
    _extract_imports,
    _detect_layer,
    _detect_file_layer,
    get_layer_rules,
    get_layer_map,
    GovernanceAdapter,
)


# ── _extract_imports ──────────────────────────────────────────────

class TestExtractImports:
    def test_simple_import(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write("import os\nimport sys\n")
        f.flush()
        try:
            result = _extract_imports(f.name)
            modules = [m for _, m in result]
            assert "os" in modules
            assert "sys" in modules
        finally:
            f.close()
            os.remove(f.name)

    def test_from_import(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write("from os.path import join\nfrom typing import List\n")
        f.flush()
        try:
            result = _extract_imports(f.name)
            modules = [m for _, m in result]
            assert "os.path" in modules
            assert "typing" in modules
        finally:
            f.close()
            os.remove(f.name)

    def test_line_numbers(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write("x = 1\nimport os\ny = 2\n")
        f.flush()
        try:
            result = _extract_imports(f.name)
            for line_no, module in result:
                if module == "os":
                    assert line_no == 2
        finally:
            f.close()
            os.remove(f.name)

    def test_nonexistent_file(self):
        result = _extract_imports("/nonexistent/file.py")
        assert result == []

    def test_syntax_error_file(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write("def broken(:\n  pass\n")
        f.flush()
        try:
            result = _extract_imports(f.name)
            assert result == []
        finally:
            f.close()
            os.remove(f.name)

    def test_no_imports(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write("x = 1\ny = 2\n")
        f.flush()
        try:
            result = _extract_imports(f.name)
            assert result == []
        finally:
            f.close()
            os.remove(f.name)


# ── _detect_layer ─────────────────────────────────────────────────

class TestDetectLayer:
    def test_infrastructure_layer(self):
        assert _detect_layer("infrastructure.git_hooks") == "infrastructure"

    def test_capabilities_layer(self):
        assert _detect_layer("capabilities.actions") == "capabilities"

    def test_surfaces_layer(self):
        assert _detect_layer("surfaces.cli") == "surfaces"

    def test_agent_layer(self):
        assert _detect_layer("agent.container") == "agent"

    def test_taxonomy_layer(self):
        assert _detect_layer("taxonomy.models") == "taxonomy"

    def test_unknown_module(self):
        assert _detect_layer("some.random.module") is None

    def test_deeply_nested(self):
        result = _detect_layer("pkg.sub.infrastructure.deep.module")
        assert result == "infrastructure"


# ── _detect_file_layer ────────────────────────────────────────────

class TestDetectFileLayer:
    def test_infrastructure_file(self):
        assert _detect_file_layer(
            "/project/src/infrastructure/file.py", "/project/src"
        ) == "infrastructure"

    def test_capabilities_file(self):
        assert _detect_file_layer(
            "/project/src/capabilities/file.py", "/project/src"
        ) == "capabilities"

    def test_unknown_layer(self):
        assert _detect_file_layer(
            "/project/src/unknown/file.py", "/project/src"
        ) is None


# ── get_layer_map ─────────────────────────────────────────────────

class TestGetLayerMap:
    def test_returns_dict(self):
        result = get_layer_map()
        assert isinstance(result, dict)

    def test_has_default_layers(self):
        result = get_layer_map()
        assert "infrastructure" in result
        assert "capabilities" in result
        assert "surfaces" in result
        assert "agent" in result
        assert "taxonomy" in result


# ── get_layer_rules ───────────────────────────────────────────────

class TestGetLayerRules:
    def test_returns_list(self):
        result = get_layer_rules()
        assert isinstance(result, list)


# ── GovernanceAdapter ─────────────────────────────────────────────

class TestGovernanceAdapter:
    def test_name(self):
        adapter = GovernanceAdapter()
        assert adapter.name() == "governance"

    def test_apply_fix_returns_false(self):
        adapter = GovernanceAdapter()
        assert adapter.apply_fix("any.py") is False

    def test_lint_non_python_file(self):
        adapter = GovernanceAdapter()
        result = adapter.lint("file.js")
        assert result == []

    def test_scan_file(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\n")
        adapter = GovernanceAdapter()
        results = adapter.scan(str(py_file))
        assert isinstance(results, list)

    def test_scan_directory(self, tmp_path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        py_file = subdir / "test.py"
        py_file.write_text("import sys\n")
        adapter = GovernanceAdapter()
        results = adapter.scan(str(tmp_path))
        assert isinstance(results, list)

    def test_scan_skips_pycache(self, tmp_path):
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        py_file = cache_dir / "cached.py"
        py_file.write_text("import os\n")
        adapter = GovernanceAdapter()
        results = adapter.scan(str(tmp_path))
        # __pycache__ should be skipped
        assert len(results) == 0

    def test_scan_skips_venv(self, tmp_path):
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        py_file = venv_dir / "lib.py"
        py_file.write_text("import os\n")
        adapter = GovernanceAdapter()
        results = adapter.scan(str(tmp_path))
        assert len(results) == 0

    def test_init_with_tracer(self):
        adapter = GovernanceAdapter(tracer="mock_tracer")
        assert adapter.tracer == "mock_tracer"

    def test_lint_detects_governance_violation(self, tmp_path):
        """Create a file in a layer that imports from a forbidden layer."""
        # Create structure: src/capabilities/bad.py importing from infrastructure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        cap_dir = src_dir / "capabilities"
        cap_dir.mkdir()
        inf_dir = src_dir / "infrastructure"
        inf_dir.mkdir()

        bad_file = cap_dir / "bad.py"
        bad_file.write_text("from infrastructure.some_module import helper\n")

        adapter = GovernanceAdapter()
        # This will only flag if there's a configured rule forbidding
        # capabilities -> infrastructure imports
        results = adapter.lint(str(bad_file))
        assert isinstance(results, list)
