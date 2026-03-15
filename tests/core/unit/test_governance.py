"""
Unit tests for the GovernanceAdapter architectural layer enforcement.
"""
import os
import tempfile
import textwrap
from unittest.mock import MagicMock


from src.core.capabilities.linting.governance import (
    GovernanceAdapter,
    _detect_layer,
    _detect_file_layer,
    _extract_imports,
    _collect_python_files,
    _resolve_root,
    GOVERNANCE_CODE,
)
from src.core._taxonomy.models import Severity


# ─── _detect_layer ────────────────────────────────────────────────────────────

def test_detect_layer_infrastructure():
    assert _detect_layer("src.infrastructure.adapters.python") == "infrastructure"

def test_detect_layer_core():
    assert _detect_layer("src.core._taxonomy.models") == "core"

def test_detect_layer_surfaces():
    assert _detect_layer("src.surfaces.mcp.server") == "surfaces"

def test_detect_layer_bootstrap():
    assert _detect_layer("src.bootstrap.container") == "bootstrap"

def test_detect_layer_unknown():
    assert _detect_layer("typing") is None

def test_detect_layer_third_party():
    assert _detect_layer("mcp.server.fastmcp") is None


# ─── _detect_file_layer ───────────────────────────────────────────────────────

def test_detect_file_layer_surfaces():
    with tempfile.TemporaryDirectory() as root:
        filepath = os.path.join(root, "src", "surfaces", "mcp", "server.py")
        result = _detect_file_layer(filepath, root)
        assert result == "surfaces"

def test_detect_file_layer_infrastructure():
    with tempfile.TemporaryDirectory() as root:
        filepath = os.path.join(root, "src", "infrastructure", "adapters", "python.py")
        result = _detect_file_layer(filepath, root)
        assert result == "infrastructure"

def test_detect_file_layer_core():
    with tempfile.TemporaryDirectory() as root:
        filepath = os.path.join(root, "src", "core", "capabilities", "action.py")
        result = _detect_file_layer(filepath, root)
        assert result == "core"

def test_detect_file_layer_unknown():
    with tempfile.TemporaryDirectory() as root:
        filepath = os.path.join(root, "tests", "some_test.py")
        result = _detect_file_layer(filepath, root)
        assert result is None


# ─── _extract_imports ─────────────────────────────────────────────────────────

def test_extract_imports_import_statement():
    code = "import src.infrastructure.adapters\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        imports = _extract_imports(path)
        assert any("infrastructure" in m for _, m in imports)
    finally:
        os.remove(path)

def test_extract_imports_from_statement():
    code = "from src.core._taxonomy.models import LintResult\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        imports = _extract_imports(path)
        assert any("core" in m for _, m in imports)
    finally:
        os.remove(path)

def test_extract_imports_syntax_error():
    code = "this is not valid python!!!\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = _extract_imports(path)
        assert result == []
    finally:
        os.remove(path)

def test_extract_imports_non_existent_file():
    result = _extract_imports("/non/existent/file.py")
    assert result == []


# ─── _collect_python_files ────────────────────────────────────────────────────

def test_collect_python_files_directory():
    with tempfile.TemporaryDirectory() as tmp:
        path1 = os.path.join(tmp, "a.py")
        path2 = os.path.join(tmp, "b.py")
        open(path1, "w").close()
        open(path2, "w").close()
        files = _collect_python_files(tmp)
        assert path1 in files
        assert path2 in files

def test_collect_python_files_single_file():
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        path = f.name
    try:
        files = _collect_python_files(path)
        assert files == [path]
    finally:
        os.remove(path)

def test_collect_python_files_skips_pycache():
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = os.path.join(tmp, "__pycache__")
        os.makedirs(cache_dir)
        cached_file = os.path.join(cache_dir, "cached.py")
        open(cached_file, "w").close()
        files = _collect_python_files(tmp)
        assert cached_file not in files

def test_collect_python_files_non_py_skipped():
    with tempfile.TemporaryDirectory() as tmp:
        js_file = os.path.join(tmp, "app.js")
        open(js_file, "w").close()
        files = _collect_python_files(tmp)
        assert js_file not in files

def test_collect_python_files_nonexistent_path():
    files = _collect_python_files("/nonexistent/path")
    assert files == []


# ─── _resolve_root ────────────────────────────────────────────────────────────

def test_resolve_root_finds_src_parent():
    with tempfile.TemporaryDirectory() as tmp:
        src_dir = os.path.join(tmp, "src")
        os.makedirs(src_dir)
        target = os.path.join(tmp, "src", "core", "some_action.py")
        root = _resolve_root(target)
        assert root == tmp


# ─── GovernanceAdapter (integration) ─────────────────────────────────────────

def test_governance_adapter_name():
    adapter = GovernanceAdapter()
    assert adapter.name() == "governance"

def test_governance_adapter_no_violations():
    """A file in surfaces that only imports from core should pass."""
    code = textwrap.dedent("""
        from src.core._taxonomy.models import LintResult
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "surfaces", "mcp")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "server.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert results == []

def test_governance_adapter_surface_imports_infrastructure():
    """Surfaces importing infrastructure directly is a CRITICAL violation."""
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "surfaces", "mcp")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "bad_tool.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)

        assert len(results) == 1
        assert results[0].code == GOVERNANCE_CODE
        assert results[0].severity == Severity.CRITICAL
        assert "surfaces" in results[0].message
        assert "infrastructure" in results[0].message

def test_governance_adapter_core_imports_infrastructure():
    """Core importing infrastructure is a CRITICAL violation."""
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python_tracer import PythonTracer
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "core", "capabilities", "linting")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "actions.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)

        assert len(results) == 1
        assert results[0].severity == Severity.CRITICAL
        assert "core" in results[0].message

def test_governance_adapter_core_imports_surfaces():
    """Core importing surfaces is forbidden."""
    code = textwrap.dedent("""
        from src.surfaces.mcp.server import main
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "core", "capabilities")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "some_action.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert len(results) == 1
        assert "surfaces" in results[0].message

def test_governance_adapter_bootstrap_is_exempt():
    """Bootstrap layer is exempt from all layer rules."""
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
        from src.surfaces.mcp.server import main
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "bootstrap")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "container.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert results == []

def test_governance_adapter_scan_single_file():
    """scan() accepts a single file path."""
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "surfaces", "mcp")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "bad.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(filepath)
        assert len(results) == 1

def test_governance_adapter_scan_skips_pycache():
    """Files in __pycache__ should not be scanned."""
    with tempfile.TemporaryDirectory() as root:
        cache_dir = os.path.join(root, "src", "surfaces", "__pycache__")
        os.makedirs(cache_dir)
        filepath = os.path.join(cache_dir, "bad.py")
        with open(filepath, "w") as f:
            f.write("from src.infrastructure.adapters.python import RuffAdapter\n")

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert results == []

def test_governance_adapter_multiple_violations():
    """Multiple violating imports in one file all reported."""
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
        import src.infrastructure.adapters.python_tracer
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "core", "capabilities")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "multi.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert len(results) == 2

def test_governance_unknown_layer_import():
    """Unrecognized target layers should be skipped."""
    code = textwrap.dedent("""
        import math
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "core")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "multi.py")
        with open(filepath, "w") as f:
            f.write(code)

        adapter = GovernanceAdapter()
        results = adapter.scan(root)
        assert len(results) == 0

def test_governance_adapter_tracer_exception():
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "surfaces", "mcp")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "bad.py")
        with open(filepath, "w") as f:
            f.write(code)

        mock_tracer = MagicMock()
        mock_tracer.trace_call_chain.side_effect = Exception("failed")
        adapter = GovernanceAdapter(tracer=mock_tracer)
        results = adapter.scan(root)
        assert len(results) == 1
        assert "infrastructure" in results[0].message
        mock_tracer.trace_call_chain.assert_called_once()

def test_resolve_root_no_src():
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "some_action.py")
        open(target, "w").close()
        root = _resolve_root(target)
        assert root == "/"

def test_governance_adapter_tracer_success():
    code = textwrap.dedent("""
        from src.infrastructure.adapters.python import RuffAdapter
    """)
    with tempfile.TemporaryDirectory() as root:
        src_dir = os.path.join(root, "src", "surfaces", "mcp")
        os.makedirs(src_dir)
        filepath = os.path.join(src_dir, "bad.py")
        with open(filepath, "w") as f:
            f.write(code)

        mock_tracer = MagicMock()
        mock_tracer.trace_call_chain.return_value = ["file.py:3 -> call()", "file2.py:4 -> call()"]
        adapter = GovernanceAdapter(tracer=mock_tracer)
        results = adapter.scan(root)
        
        # Test full resolution
        assert len(results) == 1
        assert "CallSite: file.py:3 -> call()" in results[0].related_locations

