import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from src.surfaces.mcp.tools import register_tools
from src.surfaces.mcp.server import main

def test_register_tools():
    mcp = MagicMock()
    container = MagicMock()
    
    register_tools(mcp, container)
    
    # Verify tools were registered (mcp.tool() returns a decorator)
    assert mcp.tool.call_count == 2

@pytest.mark.asyncio
async def test_mcp_tools():
    captured_tools = {}
    mcp = MagicMock()
    
    # Mock mcp.tool() decorator to capture the inner functions
    def mock_tool(*args, **kwargs):
        def decorator(func):
            captured_tools[func.__name__] = func
            return func
        return decorator
    mcp.tool.side_effect = mock_tool
    
    container = MagicMock()
    container.analysis_use_case.execute = AsyncMock(return_value=MagicMock(results=[]))
    container.analysis_use_case.to_dict.return_value = {"results": []}
    container.fixes_use_case.execute = AsyncMock(return_value="Fixes applied")
    
    register_tools(mcp, container)
    
    assert "run_lint_check" in captured_tools
    assert "apply_safe_fixes" in captured_tools
    
    # Test run_lint_check
    run_lint_check_func = captured_tools["run_lint_check"]
    result = await run_lint_check_func("some/path")
    result_dict = json.loads(result)
    assert "results" in result_dict
    container.analysis_use_case.execute.assert_called_once_with("some/path")
    
    # Test apply_safe_fixes
    apply_safe_fixes_func = captured_tools["apply_safe_fixes"]
    fix_result = await apply_safe_fixes_func("some/path")
    assert fix_result == "Fixes applied"
    container.fixes_use_case.execute.assert_called_once_with("some/path")

@patch("src.surfaces.mcp.server.FastMCP")
@patch("src.surfaces.mcp.server.get_container")
def test_server_main_function(mock_get_container, mock_fastmcp):
    mock_mcp = MagicMock()
    mock_fastmcp.return_value = mock_mcp
    
    main()
    
    mock_fastmcp.assert_called_once_with("auto-linter")
    mock_mcp.run.assert_called_once()


