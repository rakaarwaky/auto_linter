"""Comprehensive tests for agent/tracking_job_registry.py — 100% coverage."""

import pytest
from agent.tracking_job_registry import (
    create_job,
    complete_job,
    fail_job,
    list_jobs,
    get_job,
    cancel_job,
    run_with_retry,
)


class TestJobRegistry:
    def test_create_job(self):
        job_id = create_job("test_action")
        assert len(job_id) == 8
        job = get_job(job_id)
        assert job is not None
        assert job["status"] == "running"
        assert job["action"] == "test_action"
        assert "started_at" in job

    def test_complete_job(self):
        job_id = create_job("check")
        complete_job(job_id, {"score": 95.0})
        job = get_job(job_id)
        assert job["status"] == "completed"
        assert job["result"] == {"score": 95.0}
        assert "completed_at" in job

    def test_fail_job(self):
        job_id = create_job("check")
        fail_job(job_id, "Something broke")
        job = get_job(job_id)
        assert job["status"] == "failed"
        assert job["result"]["error"] == "Something broke"
        assert "completed_at" in job

    def test_list_jobs(self):
        create_job("action1")
        create_job("action2")
        jobs = list_jobs()
        assert len(jobs) >= 2

    def test_get_job_exists(self):
        job_id = create_job("check")
        job = get_job(job_id)
        assert job is not None
        assert job["action"] == "check"

    def test_get_job_not_exists(self):
        job = get_job("nonexistent")
        assert job is None

    def test_cancel_job_running(self):
        job_id = create_job("long_task")
        assert cancel_job(job_id) is True
        job = get_job(job_id)
        assert job["status"] == "cancelled"
        assert "completed_at" in job

    def test_cancel_job_not_exists(self):
        assert cancel_job("nonexistent") is False

    def test_cancel_job_already_completed(self):
        job_id = create_job("check")
        complete_job(job_id, {})
        assert cancel_job(job_id) is False

    def test_cancel_job_already_failed(self):
        job_id = create_job("check")
        fail_job(job_id, "error")
        assert cancel_job(job_id) is False

    def test_cancel_job_already_cancelled(self):
        job_id = create_job("check")
        cancel_job(job_id)
        assert cancel_job(job_id) is False


class TestRunWithRetry:
    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        async def ok():
            return "success"
        result = await run_with_retry(ok, max_retries=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        attempts = 0

        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ConnectionError("fail")
            return "recovered"

        result = await run_with_retry(flaky, max_retries=3, base_delay=0.01)
        assert result == "recovered"
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        """After max retries, should raise the last error."""
        async def always_fail():
            raise ConnectionError("always fails")

        with pytest.raises(ConnectionError, match="always fails"):
            await run_with_retry(always_fail, max_retries=2, base_delay=0.01)

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        async def timeout_once():
            raise TimeoutError("slow")

        with pytest.raises(TimeoutError):
            await run_with_retry(timeout_once, max_retries=1, base_delay=0.01)

    @pytest.mark.asyncio
    async def test_retry_on_os_error(self):
        async def os_error_once():
            raise OSError("network")

        with pytest.raises(OSError):
            await run_with_retry(os_error_once, max_retries=1, base_delay=0.01)
