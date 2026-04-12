"""Additional tests for linting_governance_adapter (infrastructure) to cover lines 8-9, 141."""


class TestLintingGovernanceAdapterImportError:
    """Test import error handling (lines 8-9)."""

    def test_import_from_lint_result_models(self):
        """Verify the module imports correctly from taxonomy."""
        from infrastructure.linting_governance_adapter import GovernanceAdapter
        adapter = GovernanceAdapter()
        assert adapter.name() == "governance"


class TestLintingGovernanceAdapterConfigMissing:
    """Test governance check when config is missing (line 141)."""

    def test_scan_with_no_config_uses_defaults(self, tmp_path):
        """When no config file exists, defaults are used."""
        import os
        import tempfile
        from infrastructure.linting_governance_adapter import GovernanceAdapter
        
        # Create a Python file in a surfaces directory
        src_dir = tmp_path / "src" / "surfaces" / "mcp"
        src_dir.mkdir(parents=True)
        py_file = src_dir / "server.py"
        py_file.write_text("from taxonomy.lint_result_models import LintResult\n")
        
        adapter = GovernanceAdapter()
        results = adapter.scan(str(tmp_path))
        # Should use default rules (empty LAYER_RULES), so no violations
        assert results == []
