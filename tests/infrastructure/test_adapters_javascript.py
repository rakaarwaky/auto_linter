import json
from unittest.mock import MagicMock, patch
from infrastructure.javascript_linter_adapter import PrettierAdapter, TSCAdapter, ESLintAdapter
from taxonomy.lint_result_models import Severity


# ========== PrettierAdapter ==========

def test_prettier_adapter_name():
    assert PrettierAdapter().name() == "prettier"


def test_prettier_adapter_scan_non_js_file():
    with patch("os.path.isfile", return_value=True):
        assert PrettierAdapter().scan("test.py") == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_prettier_adapter_scan_clean_file(mock_abs, mock_run):
    """Return [] when prettier reports exit code 0 (all clean)."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    results = PrettierAdapter().scan("test.ts")
    assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: f"/abs/{x}")
@patch("os.path.isabs", side_effect=lambda x: x.startswith("/"))
@patch("os.path.exists", return_value=True)
def test_prettier_adapter_scan_formatting_issues(mock_exists, mock_isabs, mock_abs, mock_run):
    """Return a LintResult when prettier detects formatting issues."""
    mock_run.return_value = MagicMock(returncode=1, stdout="[warn] test.ts\n", stderr="")
    results = PrettierAdapter().scan("test.ts")
    assert len(results) == 1
    assert results[0].severity == Severity.LOW
    assert results[0].code == "formatting"


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: f"/abs/{x}")
@patch("os.path.exists", return_value=False)
def test_prettier_adapter_scan_non_warn_output(mock_exists, mock_abs, mock_run):
    """If prettier fails but no [warn] in output, return []."""
    mock_run.return_value = MagicMock(returncode=1, stdout="Some other error", stderr="")
    results = PrettierAdapter().scan("test.ts")
    assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", side_effect=lambda x: "/persistent/" in x)
def test_prettier_adapter_phantom_path(mock_exists, mock_isabs, mock_abs, mock_run):
    """Phantom paths in the result should be replaced to /persistent/."""
    mock_run.return_value = MagicMock(returncode=1, stdout="[warn] file\n", stderr="")
    results = PrettierAdapter().scan("/home/raka/src/test.ts")
    assert len(results) == 1
    assert "/persistent/" in results[0].file


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", return_value=False)
def test_prettier_adapter_non_existent_fallback(mock_exists, mock_isabs, mock_abs, mock_run):
    """Non-phantom, non-existent path stays as abspath."""
    mock_run.return_value = MagicMock(returncode=1, stdout="[warn] file\n", stderr="")
    results = PrettierAdapter().scan("/other/test.ts")
    assert len(results) == 1


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
def test_prettier_adapter_exception_handling(mock_abs, mock_run):
    """General exceptions should be caught and return []."""
    mock_run.side_effect = Exception("Unexpected")
    results = PrettierAdapter().scan("test.ts")
    assert results == []


# ========== TSCAdapter ==========

def test_tsc_adapter_name():
    assert TSCAdapter().name() == "tsc"


def test_tsc_adapter_scan_non_ts_file():
    with patch("os.path.isfile", return_value=True):
        assert TSCAdapter().scan("test.py") == []


def test_tsc_adapter_phantom_path_replace():
    """TSC adapter replaces phantom /home/raka/src/ paths."""
    with patch("subprocess.run") as mock_run, \
         patch("os.path.abspath", side_effect=lambda x: x), \
         patch("os.path.exists", return_value=False):
        mock_run.return_value = MagicMock(stdout="", stderr="")
        results = TSCAdapter().scan("/home/raka/src/app.ts")
        assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", return_value=True)
def test_tsc_adapter_scan_success_pattern1(mock_exists, mock_isabs, mock_isfile, mock_abs, mock_run):
    """Pattern1: file(line,col): error TSxxxx: message"""
    tsc_output = "/abs/test.ts(10,5): error TS2304: Cannot find name 'foo'"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    results = TSCAdapter().scan("/abs/")
    assert len(results) == 1
    assert results[0].severity == Severity.HIGH
    assert results[0].code == "TS2304"
    assert results[0].line == 10


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", return_value=True)
def test_tsc_adapter_scan_success_pattern2(mock_exists, mock_isabs, mock_isfile, mock_abs, mock_run):
    """Pattern2: file:line:col - error TSxxxx: message"""
    tsc_output = "/abs/test.ts:10:5 - error TS2304: Cannot find name 'foo'"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    results = TSCAdapter().scan("/abs/")
    assert len(results) == 1
    assert results[0].severity == Severity.HIGH


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
def test_tsc_adapter_scan_no_matches(mock_isfile, mock_abs, mock_run):
    """Lines with no matching pattern are skipped."""
    mock_run.return_value = MagicMock(stdout="some random output\nanother line", stderr="")
    results = TSCAdapter().scan("/abs/")
    assert results == []


@patch("subprocess.run")
def test_tsc_adapter_general_exception(mock_run):
    """General exceptions during TSC scan should be caught."""
    mock_run.side_effect = Exception("TSC broken")
    results = TSCAdapter().scan("/abs/dir")
    assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", side_effect=lambda x: "/persistent/" in x)
@patch("os.path.isabs", return_value=True)
def test_tsc_adapter_phantom_filename_in_result(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Phantom paths in TSC output should be resolved to /persistent/."""
    tsc_output = "/home/raka/src/app.ts(3,1): error TS2304: Error"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    results = TSCAdapter().scan("/abs/")
    assert len(results) == 1
    assert "/persistent/" in results[0].file


@patch("subprocess.run")
@patch("os.path.isfile", return_value=True)
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isabs", side_effect=lambda x: not x.startswith("relative"))
@patch("os.path.exists", return_value=True)
def test_tsc_adapter_relative_filename_in_result(mock_exists, mock_isabs, mock_abs, mock_isfile, mock_run):
    """Relative paths in TSC output should be joined with scanned path base dir."""
    tsc_output = "relative/test.ts(3,1): error TS2304: Error"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    with patch("os.path.dirname", return_value="/base"), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        results = TSCAdapter().scan("/base/myfile.ts")
    assert len(results) == 1


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", return_value=False)
@patch("os.path.isabs", return_value=True)
def test_tsc_adapter_non_existent_non_phantom_path(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Non-phantom, non-existent absolute paths resolved via abspath."""
    tsc_output = "/other/test.ts(3,1): error TS2304: Error"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    results = TSCAdapter().scan("/abs/")
    assert len(results) == 1


# ========== ESLintAdapter ==========

def test_eslint_adapter_name():
    assert ESLintAdapter().name() == "eslint"


def test_eslint_adapter_scan_non_js_file():
    with patch("os.path.isfile", return_value=True):
        assert ESLintAdapter().scan("test.py") == []


def test_eslint_adapter_phantom_path_replace():
    """ESLint adapter replaces phantom /home/raka/src/ paths."""
    with patch("subprocess.run") as mock_run, \
         patch("os.path.abspath", side_effect=lambda x: x), \
         patch("os.path.exists", return_value=False):
        mock_run.return_value = MagicMock(stdout="", stderr="")
        results = ESLintAdapter().scan("/home/raka/src/app.ts")
        assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
def test_eslint_adapter_scan_empty_stdout(mock_isfile, mock_abs, mock_run):
    mock_run.return_value = MagicMock(stdout="", stderr="")
    results = ESLintAdapter().scan("/abs/dir")
    assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", return_value=True)
def test_eslint_adapter_scan_success(mock_exists, mock_isabs, mock_isfile, mock_abs, mock_run):
    eslint_output = json.dumps([
        {
            "filePath": "/abs/test.ts",
            "messages": [
                {"line": 5, "column": 2, "ruleId": "no-console", "message": "Unexpected console", "severity": 2},
                {"line": 10, "column": 1, "ruleId": "semi", "message": "Missing semicolon", "severity": 1},
            ]
        }
    ])
    mock_run.return_value = MagicMock(stdout=eslint_output, stderr="")
    results = ESLintAdapter().scan("/abs/")
    assert len(results) == 2
    assert results[0].severity == Severity.HIGH  # severity == 2
    assert results[1].severity == Severity.MEDIUM  # severity == 1


@patch("subprocess.run")
def test_eslint_adapter_general_exception(mock_run):
    """General exceptions should be caught, return []."""
    mock_run.side_effect = Exception("ESLint broken")
    results = ESLintAdapter().scan("/abs/dir")
    assert results == []


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", side_effect=lambda x: "/persistent/" in x)
@patch("os.path.isabs", return_value=True)
def test_eslint_adapter_phantom_filename_in_result(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Phantom paths in ESLint output should be resolved to /persistent/."""
    eslint_output = json.dumps([
        {
            "filePath": "/home/raka/src/app.ts",
            "messages": [
                {"line": 1, "column": 1, "ruleId": "semi", "message": "Missing semicolon", "severity": 2}
            ]
        }
    ])
    mock_run.return_value = MagicMock(stdout=eslint_output, stderr="")
    results = ESLintAdapter().scan("/abs/")
    assert len(results) == 1
    assert "/persistent/" in results[0].file


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", return_value=False)
@patch("os.path.isabs", return_value=True)
def test_eslint_adapter_non_existent_non_phantom_path(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Non-phantom, non-existent absolute paths fallback to abspath."""
    eslint_output = json.dumps([
        {
            "filePath": "/other/unknown/app.ts",
            "messages": [
                {"line": 1, "column": 1, "ruleId": "semi", "message": "Missing semicolon", "severity": 2}
            ]
        }
    ])
    mock_run.return_value = MagicMock(stdout=eslint_output, stderr="")
    results = ESLintAdapter().scan("/abs/")
    assert len(results) == 1


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: f"/abs/{x}")
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", return_value=True)
@patch("os.path.isabs", side_effect=lambda x: x.startswith("/"))
def test_eslint_adapter_relative_filepath_in_result(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Relative paths in ESLint output should be made absolute."""
    eslint_output = json.dumps([
        {
            "filePath": "relative/test.ts",
            "messages": [
                {"line": 1, "column": 1, "ruleId": "semi", "message": "Missing semicolon", "severity": 2}
            ]
        }
    ])
    mock_run.return_value = MagicMock(stdout=eslint_output, stderr="")
    results = ESLintAdapter().scan("/abs/")
    assert len(results) == 1


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isabs", return_value=True)
@patch("os.path.exists", return_value=False)
def test_prettier_adapter_phantom_second_fallback(mock_exists, mock_isabs, mock_abs, mock_run):
    """Secondary fallback for Prettier phantom path."""
    mock_run.return_value = MagicMock(returncode=1, stdout="[warn] file\n", stderr="")
    exists_calls = []
    def mock_exists_side_effect(path):
        exists_calls.append(path)
        # 1. alt_path check
        # 2. filename check
        # 3. project_file check
        return len(exists_calls) >= 3
    
    with patch("os.path.exists", side_effect=mock_exists_side_effect):
        results = PrettierAdapter().scan("/home/raka/src/test.ts")
        assert len(results) == 1
        assert "/persistent/" in results[0].file


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", return_value=False)
@patch("os.path.isabs", return_value=True)
def test_tsc_adapter_phantom_second_fallback(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Secondary fallback for TSC phantom path."""
    tsc_output = "/home/raka/src/app.ts(3,1): error TS2304: Error"
    mock_run.return_value = MagicMock(stdout=tsc_output, stderr="")
    exists_calls = []
    def mock_exists_side_effect(path):
        exists_calls.append(path)
        return len(exists_calls) >= 3
    
    with patch("os.path.exists", side_effect=mock_exists_side_effect):
        results = TSCAdapter().scan("/abs/")
        assert len(results) == 1
        assert "/persistent/" in results[0].file


@patch("subprocess.run")
@patch("os.path.abspath", side_effect=lambda x: x)
@patch("os.path.isfile", return_value=False)
@patch("os.path.exists", return_value=False)
@patch("os.path.isabs", return_value=True)
def test_eslint_adapter_phantom_second_fallback(mock_isabs, mock_exists, mock_isfile, mock_abs, mock_run):
    """Secondary fallback for ESLint phantom path."""
    eslint_output = json.dumps([
        {
            "filePath": "/home/raka/src/app.ts",
            "messages": [
                {"line": 1, "column": 1, "ruleId": "semi", "message": "Missing semicolon", "severity": 2}
            ]
        }
    ])
    mock_run.return_value = MagicMock(stdout=eslint_output, stderr="")
    exists_calls = []
    def mock_exists_side_effect(path):
        exists_calls.append(path)
        return len(exists_calls) >= 3
    
    with patch("os.path.exists", side_effect=mock_exists_side_effect):
        results = ESLintAdapter().scan("/abs/")
        assert len(results) == 1
        assert "/persistent/" in results[0].file
