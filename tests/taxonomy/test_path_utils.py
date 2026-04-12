import os
from taxonomy.relative_path_resolver import normalize_path

from unittest.mock import patch

def test_normalize_path_empty():
    assert normalize_path("") == ""
    assert normalize_path(None) is None

def test_normalize_path_slashes():
    assert normalize_path("C:\\foo\\\\bar") == "C:/foo/bar"

def test_normalize_path_phantom_root():
    path = "/home/raka/src/core/models.py"
    expected = "/persistent/home/raka/mcp-servers/auto_linter/src/core/models.py"
    with patch.dict("os.environ", {
        "PHANTOM_ROOT": "/home/raka/src/",
        "PROJECT_ROOT": "/persistent/home/raka/mcp-servers/auto_linter/src/"
    }):
        assert normalize_path(path) == expected

def test_normalize_path_relative_src():
    # Mock current working directory to contain auto_linter
    try:
        # We target the actual path resolution logic
        res = normalize_path("src/core/models.py")
        assert os.path.isabs(res)
        assert "src/core/models.py" in res
    finally:
        pass
