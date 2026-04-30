import os
import tempfile
from infrastructure.python_ast_tracer import PythonTracer

def test_build_variants():
    variants = PythonTracer().build_variants("process_payment")
    assert "process_payment" in variants
    assert "PROCESS_PAYMENT" in variants
    assert "processPayment" in variants
    assert "ProcessPayment" in variants
    assert "process-payment" in variants
    
def test_show_enclosing_scope():
    code = """
class MyPaymentProcess:
    def execute(self):
        x = 1
        y = 2
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f_path = f.name
        
    try:
        scope = PythonTracer().show_enclosing_scope(f_path, 4)
        assert scope == "class MyPaymentProcess -> def execute"
    finally:
        os.remove(f_path)
        
def test_find_flow():
    code = """
def test_flow():
    data = []
    data.append(1)
    print(data)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f_path = f.name
        
    try:
        flows = PythonTracer().find_flow(f_path, "data", start_line=2)
        assert len(flows) >= 3
        assert "Assignment" in flows[0]
        assert "Mutation" in flows[1]
        assert "Usage" in flows[2]
    finally:
        os.remove(f_path)
        
def test_trace_call_chain():
    code1 = """
def my_func():
    pass
"""
    code2 = """
from my_module import my_func

def caller():
    my_func()
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        path1 = os.path.join(temp_dir, "my_module.py")
        path2 = os.path.join(temp_dir, "caller_module.py")
        with open(path1, "w") as f:
            f.write(code1)
        with open(path2, "w") as f:
            f.write(code2)
            
        callers = PythonTracer().trace_call_chain(temp_dir, "my_func")
        assert len(callers) == 1
        assert "caller_module.py" in callers[0]
        assert "my_func()" in callers[0]

def test_get_variant_dict():
    variants = PythonTracer().get_variant_dict("process_payment")
    assert variants["snake_case"] == "process_payment"
    assert variants["camel_case"] == "processPayment"
    assert variants["pascal_case"] == "ProcessPayment"
    assert variants["screaming_snake"] == "PROCESS_PAYMENT"

def test_project_wide_rename():
    code = "badVar = 1\nresult = badVar + 1\n# badVar is used here\nprint('badVar is great')\n"
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "sample.py")
        with open(path, "w") as f:
            f.write(code)

        modified = PythonTracer().project_wide_rename(temp_dir, "badVar", "good_var")
        assert modified == 1

        with open(path, "r") as f:
            result = f.read()

        # Code identifiers should be renamed
        assert "good_var = 1" in result
        assert "result = good_var + 1" in result
        # String literal should NOT be renamed
        assert "'badVar is great'" in result
