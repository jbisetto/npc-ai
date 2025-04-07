"""
Tests for the usage tracking and quota management system.

This module tests the functionality of the UsageTracker, UsageQuota,
and UsageRecord classes for basic usage tracking.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.ai.npc.hosted.usage_tracker import UsageTracker, UsageQuota, UsageRecord
from src.ai.npc.config import get_config

# Test fixtures
@pytest.fixture
def test_storage_path(tmp_path) -> Path:
    """Create a temporary storage path for testing."""
    return tmp_path / "test_usage.json"

@pytest.fixture
def test_quota() -> UsageQuota:
    """Create a test quota configuration."""
    return UsageQuota(
        daily_token_limit=1000,
        hourly_request_limit=10,
        monthly_cost_limit=5.0,
        cost_per_1k_input_tokens={"test-model": 0.001, "default": 0.002},
        cost_per_1k_output_tokens={"test-model": 0.002, "default": 0.004}
    )

@pytest.fixture
def tracker(test_storage_path, test_quota) -> UsageTracker:
    """Create a test usage tracker."""
    return UsageTracker(quota=test_quota, storage_path=str(test_storage_path))

# Basic functionality tests
def test_usage_quota_initialization():
    """Test UsageQuota initialization with custom values."""
    quota = UsageQuota(
        daily_token_limit=5000,
        hourly_request_limit=20,
        monthly_cost_limit=10.0
    )
    assert quota.daily_token_limit == 5000
    assert quota.hourly_request_limit == 20
    assert quota.monthly_cost_limit == 10.0
    assert isinstance(quota.cost_per_1k_input_tokens, dict)
    assert isinstance(quota.cost_per_1k_output_tokens, dict)

def test_usage_record_serialization():
    """Test UsageRecord serialization and deserialization."""
    timestamp = datetime.now()
    record = UsageRecord(
        timestamp=timestamp,
        request_id="test-123",
        model_id="test-model",
        input_tokens=100,
        output_tokens=50,
        duration_ms=1500,
        success=True
    )
    
    # Test serialization
    record_dict = record.to_dict()
    assert record_dict["request_id"] == "test-123"
    assert record_dict["model_id"] == "test-model"
    assert record_dict["input_tokens"] == 100
    assert record_dict["output_tokens"] == 50
    
    # Test deserialization
    new_record = UsageRecord.from_dict(record_dict)
    assert new_record.request_id == record.request_id
    assert new_record.model_id == record.model_id
    assert new_record.input_tokens == record.input_tokens
    assert new_record.output_tokens == record.output_tokens

# Usage tracking tests
@pytest.mark.asyncio
async def test_track_usage(tracker):
    """Test basic usage tracking functionality."""
    record = await tracker.track_usage(
        request_id="test-123",
        model_id="test-model",
        input_tokens=100,
        output_tokens=50,
        duration_ms=1500
    )
    
    assert record.request_id == "test-123"
    assert record.model_id == "test-model"
    assert record.input_tokens == 100
    assert record.output_tokens == 50
    assert record.success is True
    assert record.error_type is None
    
    # Verify record was added to tracker
    assert len(tracker.records) == 1
    assert tracker.records[0].request_id == "test-123"

@pytest.mark.asyncio
async def test_track_failed_usage(tracker):
    """Test tracking failed API calls."""
    record = await tracker.track_usage(
        request_id="fail-123",
        model_id="test-model",
        input_tokens=100,
        output_tokens=0,
        duration_ms=500,
        success=False,
        error_type="QuotaExceeded"
    )
    
    assert record.success is False
    assert record.error_type == "QuotaExceeded"
    assert record.output_tokens == 0

# Concurrent access tests
@pytest.mark.asyncio
async def test_concurrent_access(tracker):
    """Test thread-safe concurrent access."""
    async def make_request(request_id: str):
        return await tracker.track_usage(
            request_id=request_id,
            model_id="test-model",
            input_tokens=100,
            output_tokens=50,
            duration_ms=1500
        )
    
    # Make multiple concurrent requests
    tasks = [make_request(f"concurrent-{i}") for i in range(5)]
    records = await asyncio.gather(*tasks)
    
    # Verify all requests were tracked
    assert len(tracker.records) == 5
    assert len({r.request_id for r in records}) == 5  # All unique 