# Purpose: Fix Python path for test environment
# Issue:   Tests failed because modules were not found (PYTHONPATH not set)
# Solution: Add src/ to sys.path when pytest runs

import sys
import os

# Tambahkan src/ ke Python path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set PHANTOM_ROOT and PROJECT_ROOT for path normalization tests
# Force-override (not setdefault) to ensure test consistency
os.environ["PHANTOM_ROOT"] = "/home/raka/src/"
os.environ["PROJECT_ROOT"] = "/persistent/home/raka/mcp-servers/auto_linter/src/"