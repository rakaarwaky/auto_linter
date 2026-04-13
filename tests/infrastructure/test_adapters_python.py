import json
import pytest
from unittest.mock import MagicMock, patch
from infrastructure import RuffAdapter, MyPyAdapter
from taxonomy.lint_result_models import Severity

# ========== RuffAdapter ==========

def test_ruff_adapter_name():
    assert RuffAdapter().name() == "ruff"

def test_ruff_adapter_scan_json_error_after_bracket():
    adapter = RuffAdapter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Noise [ invalid json ]", stderr="", returncode=0)
        results = adapter.scan("test.py")
        assert results == []

def test_ruff_adapter_scan_empty_stdout():
    adapter = RuffAdapter()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="  ", stderr="", returncode=0)
        results = adapter.scan("test.py")
        assert results == []

def test_ruff_adapter_scan_non_python_file():
    with patch("os.path.isfile", return_value=True):
        assert RuffAdapter().scan("test.txt") == []

@patch("subprocess.run")
@patch("os.path.abspath")
@patch("os.path.exists")
def test_ruff_adapter_scan_success(mock_exists, mock_abs, mock_run):
    mock_abs.side_effect = lambda x: f"/abs/{x}"
    mock_exists.return_value = True

    ruff_output = json.dumps([
        {
            "filename": "test.py",
            "location": {"row": 1, "column": 1},
            "code": "E901",
            "message": "Syntax error"
        },
        {
            "filename": "test.py",
            "location": {"row": 5, "column": 1},
            "code": "W291",
            "message": "Trailing whitespace"
        },
        {
            "filename": "test.py",
            "location": {"row": 10, "column": 1},
            "code": "F401",
            "message": "Unused import"
        }
    ])
    mock_run.return_value = MagicMock(stdout=ruff_output, stderr="")

    adapter = RuffAdapter()
    results = adapter.scan("test.py")

    assert len(results) == 3
    assert results[0].severity == Severity.HIGH   # E901
    assert results[1].severity == Severity.LOW    # W291
    assert results[2].severity == Severity.HIGH   # F401

@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
def test_ruff_adapter_empty_stdout(mock_isfile, mock_abs, mock_run):
    mock_run.return_value = MagicMock(stdout="", stderr="")
    results = RuffAdapter().scan("some/dir")
    assert results == []

@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
def test_ruff_adapter_json_decode_error(mock_isfile, mock_abs, mock_run):
    """Should return [] if stdout is un-parseable JSON."""
    mock_run.return_value = MagicMock(stdout="not-json-output", stderr="")
    results = RuffAdapter().scan("some/dir")
    assert results == []

@patch("subprocess.run", side_effect=FileNotFoundError)
def test_ruff_adapter_file_not_found(mock_run):
    """Should return [] gracefully when ruff binary is missing."""
    results = RuffAdapter().scan("test.py")
    assert results == []

@patch("subprocess.run")
def test_ruff_adapter_scan_e902_real_file_missing(mock_run):
    """E902 errors where both phantom and real paths don't exist should be filtered."""
    ruff_output = json.dumps([
        {
            "filename": "/home/raka/src/ghost.py",
            "location": {"row": 1, "column": 1},
            "code": "E902",
            "message": "File not found"
        }
    ])
    ruff_stdout = "No such file or directory\n" + ruff_output
    mock_run.return_value = MagicMock(stdout=ruff_stdout, stderr="")

    with patch("os.path.exists", return_value=False):
        results = RuffAdapter().scan("some/path")
        assert results == []

@patch("subprocess.run")
def test_ruff_adapter_scan_e902_mixed_real_errors(mock_run):
    """Non-E902 errors should still be processed even when E902 phantom filter runs."""
    ruff_output = json.dumps([
        {
            "filename": "/home/raka/src/test.py",
            "location": {"row": 1, "column": 1},
            "code": "E902",
            "message": "File not found"
        },
        {
            "filename": "/abs/test.py",
            "location": {"row": 5, "column": 2},
            "code": "E501",
            "message": "Line too long"
        }
    ])
    # Must contain both for the code at line 31 to trigger
    ruff_stdout = "No such file or directory\nE902\n" + ruff_output
    mock_run.return_value = MagicMock(stdout=ruff_stdout, stderr="")

    # Mock exists to return False for phantom, so it gets filtered
    with patch("os.path.exists", return_value=False), \
         patch("os.path.abspath", side_effect=lambda x: x), \
         patch("os.path.isabs", return_value=True):
        results = RuffAdapter().scan("/abs/")
        # E902 is filtered (as it doesn't exist), E501 remains (even if it doesn't exist either, it's not E902)
        assert len(results) == 1
        assert results[0].code == "E501"

# ========== MyPyAdapter ==========

def test_mypy_adapter_name():
    assert MyPyAdapter().name() == "mypy"

def test_mypy_adapter_scan_non_python_file():
    with patch("os.path.isfile", return_value=True):
        assert MyPyAdapter().scan("test.txt") == []

@patch("subprocess.run")
@patch("os.path.exists")
def test_mypy_adapter_scan_success(mock_exists, mock_run):
    mock_exists.return_value = True
    mypy_output = "test.py:10:5: error: Incompatible types\ntest.py:20: note: See here\ntest.py:30:1: warning: Maybe wrong"
    mock_run.return_value = MagicMock(stdout=mypy_output, stderr="")

    adapter = MyPyAdapter()
    results = adapter.scan("test.py")

    assert len(results) == 3
    assert results[0].severity == Severity.HIGH
    assert results[0].line == 10
    assert results[1].severity == Severity.INFO
    assert results[1].line == 20
    assert results[2].severity == Severity.MEDIUM  # warning

@patch("subprocess.run", side_effect=FileNotFoundError)
def test_mypy_adapter_file_not_found(mock_run):
    """Should return [] gracefully when mypy binary is missing."""
    results = MyPyAdapter().scan("test.py")
    assert results == []

@patch("subprocess.run")
@patch("os.path.isfile", return_value=False)
def test_mypy_adapter_empty_output(mock_isfile, mock_run):
    mock_run.return_value = MagicMock(stdout="", stderr="")
    adapter = MyPyAdapter()
    results = adapter.scan("/some/dir")
    assert results == []

@patch("subprocess.run")
@patch("os.path.exists", return_value=False)
@patch("os.path.isabs", return_value=True)
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
def test_mypy_adapter_non_existent_file_abspath(mock_isfile, mock_abs, mock_isabs, mock_exists, mock_run):
    """Non-existent files (not phantom) should be resolved to abspath."""
    mypy_output = "/other/path/app.py:5:1: error: Some error"
    mock_run.return_value = MagicMock(stdout=mypy_output, stderr="")
    results = MyPyAdapter().scan("/any/dir")
    assert len(results) == 1

@patch("subprocess.run")
@patch("os.path.isfile", return_value=True)
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.exists", return_value=True)
def test_mypy_adapter_relative_filename_in_output(mock_exists, mock_abs, mock_isfile, mock_run):
    """Relative file paths in mypy output should be made absolute relative to scanned path's dir."""
    mypy_output = "subdir/test.py:10:5: error: Some error"
    mock_run.return_value = MagicMock(stdout=mypy_output, stderr="")
    with patch("os.path.isabs", side_effect=lambda x: x.startswith("/")), \
         patch("os.path.dirname", return_value="/base"), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        results = MyPyAdapter().scan("/base/test.py")
    assert len(results) == 1

@patch("subprocess.run")
def test_ruff_adapter_scan_generic_exception(mock_run):
    mock_run.side_effect = Exception("test error")
    results = RuffAdapter().scan("test.py")
    assert results == []

@patch("subprocess.run")
@patch("os.path.isabs", return_value=False)
@patch("os.path.exists", side_effect=[False, True]) # first exists fails, second (abspath) succeeds
@patch("os.path.abspath", side_effect=lambda x: f"/abs/{x}")
def test_ruff_adapter_scan_relative_abspath_fallback(mock_abs, mock_exists, mock_isabs, mock_run):
    mock_run.return_value = MagicMock(stdout=json.dumps([{"filename": "rel.py", "location": {"row": 1, "column": 1}, "code": "E100", "message": "msg"}]), stderr="")
    results = RuffAdapter().scan("/dir/")
    assert len(results) == 1
    assert results[0].file == "/abs/rel.py"

@patch("subprocess.run")
def test_mypy_adapter_scan_generic_exception(mock_run):
    mock_run.side_effect = Exception("test error")
    results = MyPyAdapter().scan("test.py")
    assert results == []

@patch("subprocess.run")
def test_ruff_adapter_custom_bin_path(mock_run):
    mock_run.return_value = MagicMock(stdout="[]", stderr="")
    adapter = RuffAdapter(bin_path="/custom/bin")
    results = adapter.scan("test.py")
    assert results == []

@patch("subprocess.run")
def test_ruff_adapter_json_decode_split_empty(mock_run):
    mock_run.return_value = MagicMock(stdout="Noise [", stderr="")
    adapter = RuffAdapter()
    results = adapter.scan("test.py")
    assert results == []

@patch("subprocess.run")
def test_mypy_adapter_custom_bin_path(mock_run):
    mock_run.return_value = MagicMock(stdout="", stderr="")
    adapter = MyPyAdapter(bin_path="/custom/bin")
    results = adapter.scan("test.py")
    assert results == []
