"""Additional tests for tracking_job_registry to cover line 83."""

import pytest
from agent.tracking_job_registry import run_with_retry


class TestTrackingJobRegistryUncovered:
    """Tests for uncovered line 83 (run_with_retry with failures)."""

    @pytest.mark.asyncio
    async def test_run_with_retry_value_error_not_retried(self):
        """ValueError is not in the retryable exceptions list."""
        async def fail_with_value_error():
            raise ValueError("not retryable")

        with pytest.raises(ValueError, match="not retryable"):
            await run_with_retry(fail_with_value_error, max_retries=3, base_delay=0.01)

    @pytest.mark.asyncio
    async def test_run_with_retry_type_error_not_retried(self):
        """TypeError is not in the retryable exceptions list."""
        async def fail_with_type_error():
            raise TypeError("not retryable")

        with pytest.raises(TypeError, match="not retryable"):
            await run_with_retry(fail_with_type_error, max_retries=3, base_delay=0.01)

    @pytest.mark.asyncio
    async def test_run_with_retry_all_retries_fail(self):
        """After all retries exhausted with ConnectionError."""
        call_count = 0
        
        async def always_fail_connection():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("always fails")

        with pytest.raises(ConnectionError, match="always fails"):
            await run_with_retry(always_fail_connection, max_retries=2, base_delay=0.01)
        
        # Should have tried max_retries times
        assert call_count == 2
