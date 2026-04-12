# Tujuan:  Fix Python path untuk test environment
# Masalah: Test gagal karena module tidak ditemukan (PYTHONPATH tidak diset)
# Solusi:  Tambahkan src/ ke sys.path saat pytest berjalan

import sys
import os

# Tambahkan src/ ke Python path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set PHANTOM_ROOT and PROJECT_ROOT for path normalization tests
os.environ.setdefault("PHANTOM_ROOT", "/home/raka/src/")
os.environ.setdefault(
    "PROJECT_ROOT",
    "/persistent/home/raka/mcp-servers/auto_linter/src/"
)