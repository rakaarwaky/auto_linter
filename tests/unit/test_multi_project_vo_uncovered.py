"""Additional tests for multi_project_vo to cover line 52."""

from taxonomy.multi_project_vo import AggregatedResults, ProjectResult


class TestMultiProjectVOUncovered:
    """Tests for uncovered line 52 (MultiProjectReport error text output)."""

    def test_aggregated_results_to_text_with_errors(self):
        """Test error text output (line 52)."""
        projects = [
            ProjectResult(
                path="/project/a",
                score=0.0,
                is_passing=False,
                error="Lint failed: Connection refused",
            ),
            ProjectResult(
                path="/project/b",
                score=85.0,
                is_passing=True,
            ),
        ]
        
        results = AggregatedResults(
            projects=projects,
            total_projects=2,
            passing_projects=1,
            failing_projects=1,
            average_score=85.0,
        )
        
        text = results.to_text()
        assert "ERROR" in text
        assert "Lint failed" in text
        assert "/project/b" in text
        assert "85.0" in text

    def test_aggregated_results_to_text_all_errors(self):
        """Test text output when all projects have errors."""
        projects = [
            ProjectResult(path="/p1", score=0.0, is_passing=False, error="Error 1"),
            ProjectResult(path="/p2", score=0.0, is_passing=False, error="Error 2"),
        ]
        
        results = AggregatedResults(
            projects=projects,
            total_projects=2,
            passing_projects=0,
            failing_projects=2,
            average_score=0.0,
        )
        
        text = results.to_text()
        assert text.count("ERROR") == 2
        assert "Error 1" in text
        assert "Error 2" in text
