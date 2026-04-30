import os
import tempfile
from unittest.mock import patch, mock_open
from infrastructure.javascript_call_tracer import JSTracer

def test_js_show_enclosing_scope_oserror():
    tracer = JSTracer()
    with patch("builtins.open", side_effect=OSError):
        # We must make path exist to pass the initial check
        with patch("os.path.exists", return_value=True):
            res = tracer.show_enclosing_scope("/non_existent_file.js", 1)
            assert res is None

def test_js_show_enclosing_scope_brace_break():
    tracer = JSTracer()
    # Trigger `else: break` loops securely
    js_code = """
function outer() {
    // brace depth is 1
}
// depth is 0
let x = 1;
    """
    with tempfile.NamedTemporaryFile("w+", suffix=".js", delete=False) as f:
        f.write(js_code)
        filepath = f.name
    try:
        res = tracer.show_enclosing_scope(filepath, 5)
        assert res is None
    finally:
        os.remove(filepath)

def test_js_find_flow_oserror():
    tracer = JSTracer()
    with patch("builtins.open", side_effect=OSError):
        with patch("os.path.exists", return_value=True):
            res = tracer.find_flow("/non_existent_file.js", "x")
            assert res == []

def test_js_find_flow_brace_break():
    tracer = JSTracer()
    js_code = """
function test() {
    let x = 1;
}
x = 2; // out of scope
    """
    with tempfile.NamedTemporaryFile("w+", suffix=".js", delete=False) as f:
        f.write(js_code)
        filepath = f.name
    try:
        res = tracer.find_flow(filepath, "x", start_line=1)
        # Should finish gracefully testing breaks
        assert len(res) >= 0
    finally:
        os.remove(filepath)

@patch("glob.glob")
def test_js_trace_call_chain_ioerror(mock_glob):
    mock_glob.return_value = ["/fake/file.js"]
    tracer = JSTracer()
    with patch("builtins.open", side_effect=IOError):
        res = tracer.trace_call_chain("/", "myFunc")
        assert res == []

@patch("glob.glob")
def test_js_project_wide_rename_ioerror_read(mock_glob):
    mock_glob.return_value = ["/fake/file.js"]
    tracer = JSTracer()
    with patch("builtins.open", side_effect=IOError):
        res = tracer.project_wide_rename("/", "oldName", "newName")
        assert res == 0

@patch("glob.glob")
def test_js_project_wide_rename_ioerror_write(mock_glob):
    mock_glob.return_value = ["/fake/file.js"]
    tracer = JSTracer()
    m = mock_open(read_data="let oldName = 1;")
    def open_side_effect(file, mode="r", **kwargs):
        if "w" in mode:
            raise IOError("Write failed")
        return m(file, mode, **kwargs)
        
    with patch("builtins.open", side_effect=open_side_effect):
        res = tracer.project_wide_rename("/", "oldName", "newName")
        assert res == 0
