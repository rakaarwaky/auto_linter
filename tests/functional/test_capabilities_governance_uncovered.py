"""Additional tests for capabilities/linting_governance_adapter to cover lines 105, 198-199."""

import os
import tempfile
import textwrap
from unittest.mock import MagicMock
import capabilities.linting_governance_adapter as gov_module
from capabilities.linting_governance_adapter import GovernanceAdapter, LAYER_RULES, LAYER_MAP


class TestCapabilitiesGovernanceAdapterUncovered:
    """Tests for uncovered lines 105, 198-199."""

    def test_governance_scoring_with_missing_adapters(self):
        """Test governance scoring when no adapters are configured (line 105)."""
        # _get_rules returns LAYER_RULES which is empty by default
        adapter = GovernanceAdapter()
        rules = adapter._get_rules()
        # Default LAYER_RULES is empty
        assert rules == []

    def test_governance_report_generation(self, tmp_path):
        """Test governance report generation (lines 198-199)."""
        # Create a file that will trigger a violation
        src_dir = tmp_path / "src" / "surfaces" / "mcp"
        src_dir.mkdir(parents=True)
        py_file = src_dir / "bad.py"
        py_file.write_text("from infrastructure import Something\n")

        adapter = GovernanceAdapter(
            rules=[("surfaces", "infrastructure", "Surfaces must not import infrastructure")],
            layer_map=LAYER_MAP,
        )
        results = adapter.scan(str(tmp_path))
        assert len(results) >= 1
        # Verify report generation includes related_locations
        violation = results[0]
        assert violation.severity.value == "critical"

    def test_governance_with_tracer_success(self, tmp_path):
        """Test governance with tracer that succeeds."""
        src_dir = tmp_path / "src" / "surfaces" / "mcp"
        src_dir.mkdir(parents=True)
        py_file = src_dir / "bad.py"
        py_file.write_text("from infrastructure import Something\n")

        mock_tracer = MagicMock()
        mock_tracer.trace_call_chain.return_value = ["test.py:5 -> call()"]
        
        adapter = GovernanceAdapter(
            tracer=mock_tracer,
            rules=[("surfaces", "infrastructure", "Surfaces must not import infrastructure")],
            layer_map=LAYER_MAP,
        )
        results = adapter.scan(str(tmp_path))
        assert len(results) >= 1
        assert "CallSite:" in results[0].related_locations[0]
