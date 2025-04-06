"""
Usage tracking and quota management for Amazon Bedrock.

This module provides utilities for tracking API usage, enforcing quotas,
and managing costs for Amazon Bedrock API calls.
"""

import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from src.ai.npc.config import get_config

# Set up logging
logger = logging.getLogger(__name__)

class UsageQuota:
    """Configuration for usage quotas."""
    
    def __init__(
        self,
        daily_token_limit: Optional[int] = None,
        hourly_request_limit: Optional[int] = None,
        monthly_cost_limit: Optional[float] = None,
        cost_per_1k_input_tokens: Optional[Dict[str, float]] = None,
        cost_per_1k_output_tokens: Optional[Dict[str, float]] = None
    ):
        """
        Initialize usage quota configuration.
        
        Args:
            daily_token_limit: Maximum tokens per day
            hourly_request_limit: Maximum requests per hour
            monthly_cost_limit: Maximum cost per month in USD
            cost_per_1k_input_tokens: Cost per 1000 input tokens by model
            cost_per_1k_output_tokens: Cost per 1000 output tokens by model
        """
        # Load values from configuration, with fallbacks to parameters or defaults
        self.daily_token_limit = daily_token_limit or get_config("tier3.usage_tracker.daily_token_limit", 100000)
        self.hourly_request_limit = hourly_request_limit or get_config("tier3.usage_tracker.hourly_request_limit", 100)
        self.monthly_cost_limit = monthly_cost_limit or get_config("tier3.usage_tracker.monthly_cost_limit", 50.0)
        
        # Load pricing information from configuration
        self.cost_per_1k_input_tokens = cost_per_1k_input_tokens or get_config(
            "tier3.usage_tracker.cost_per_1k_input_tokens",
            {
                "amazon.nova-micro-v1:0": 0.0003,
                "amazon.titan-text-express-v1": 0.0008,
                "anthropic.claude-3-sonnet-20240229-v1:0": 0.003,
                "anthropic.claude-3-haiku-20240307-v1:0": 0.00025,
                "default": 0.001  # Default fallback price
            }
        )
        
        self.cost_per_1k_output_tokens = cost_per_1k_output_tokens or get_config(
            "tier3.usage_tracker.cost_per_1k_output_tokens",
            {
                "amazon.nova-micro-v1:0": 0.0006,
                "amazon.titan-text-express-v1": 0.0016,
                "anthropic.claude-3-sonnet-20240229-v1:0": 0.015,
                "anthropic.claude-3-haiku-20240307-v1:0": 0.00125,
                "default": 0.002  # Default fallback price
            }
        )


class UsageRecord:
    """Record of a single API usage."""
    
    def __init__(
        self,
        timestamp: datetime,
        request_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        success: bool,
        error_type: Optional[str] = None
    ):
        """
        Initialize a usage record.
        
        Args:
            timestamp: When the API call was made
            request_id: The ID of the request
            model_id: The model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Duration of the API call in milliseconds
            success: Whether the API call was successful
            error_type: Type of error if the call failed
        """
        self.timestamp = timestamp
        self.request_id = request_id
        self.model_id = model_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.duration_ms = duration_ms
        self.success = success
        self.error_type = error_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_type": self.error_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageRecord':
        """Create a record from a dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            request_id=data["request_id"],
            model_id=data["model_id"],
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            duration_ms=data["duration_ms"],
            success=data["success"],
            error_type=data["error_type"]
        )


class UsageTracker:
    """Tracks API usage and enforces quotas."""
    
    def __init__(
        self,
        quota: UsageQuota = None,
        storage_path: Optional[str] = None,
        auto_save: Optional[bool] = None
    ):
        """
        Initialize the usage tracker.
        
        Args:
            quota: Usage quota configuration
            storage_path: Path to store usage data
            auto_save: Whether to automatically save usage data
        """
        self.quota = quota or UsageQuota()
        self.storage_path = storage_path or get_config("tier3.usage_tracker.storage_path", "data/usage/bedrock_usage.json")
        self.auto_save = auto_save if auto_save is not None else get_config("tier3.usage_tracker.auto_save", True)
        self.records: List[UsageRecord] = []
        self.lock = asyncio.Lock()
        
        # Load existing records if storage path is provided
        if self.storage_path:
            self._load_records()
    
    async def track_usage(
        self,
        request_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        success: bool = True,
        error_type: Optional[str] = None
    ) -> UsageRecord:
        """
        Track API usage.
        
        Args:
            request_id: The ID of the request
            model_id: The model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Duration of the API call in milliseconds
            success: Whether the API call was successful
            error_type: Type of error if the call failed
            
        Returns:
            The created usage record
        """
        async with self.lock:
            # Create a new record
            record = UsageRecord(
                timestamp=datetime.now(),
                request_id=request_id,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                success=success,
                error_type=error_type
            )
            
            # Add the record to the list
            self.records.append(record)
            
            # Log the usage
            logger.info(
                f"API usage: model={model_id}, input_tokens={input_tokens}, "
                f"output_tokens={output_tokens}, duration={duration_ms}ms, "
                f"success={success}"
            )
            
            # Save records if auto-save is enabled
            if self.auto_save and self.storage_path:
                await self._save_records()
            
            return record
    
    async def check_quota(self, model_id: str, estimated_tokens: int) -> Tuple[bool, str]:
        """
        Check if a request would exceed the quota.
        
        Args:
            model_id: The model to use
            estimated_tokens: Estimated number of tokens for the request
            
        Returns:
            A tuple of (allowed, reason)
        """
        async with self.lock:
            # Check daily token limit
            daily_tokens = self.get_token_usage_for_period(timedelta(days=1))
            if daily_tokens + estimated_tokens > self.quota.daily_token_limit:
                return False, f"Daily token limit exceeded ({daily_tokens}/{self.quota.daily_token_limit})"
            
            # Check hourly request limit
            hourly_requests = self.get_request_count_for_period(timedelta(hours=1))
            if hourly_requests >= self.quota.hourly_request_limit:
                return False, f"Hourly request limit exceeded ({hourly_requests}/{self.quota.hourly_request_limit})"
            
            # Check monthly cost limit
            monthly_cost = self.get_cost_for_period(timedelta(days=30))
            estimated_cost = self._estimate_cost(model_id, estimated_tokens, estimated_tokens)
            if monthly_cost + estimated_cost > self.quota.monthly_cost_limit:
                return False, f"Monthly cost limit exceeded (${monthly_cost:.2f}/${self.quota.monthly_cost_limit:.2f})"
            
            return True, "Quota check passed"
    
    def get_token_usage_for_period(self, period: timedelta) -> int:
        """
        Get the total token usage for a period.
        
        Args:
            period: The time period to check
            
        Returns:
            Total tokens used in the period
        """
        cutoff = datetime.now() - period
        return sum(
            record.input_tokens + record.output_tokens
            for record in self.records
            if record.timestamp >= cutoff and record.success
        )
    
    def get_request_count_for_period(self, period: timedelta) -> int:
        """
        Get the number of requests for a period.
        
        Args:
            period: The time period to check
            
        Returns:
            Number of requests in the period
        """
        cutoff = datetime.now() - period
        return sum(
            1 for record in self.records
            if record.timestamp >= cutoff
        )
    
    def get_cost_for_period(self, period: timedelta) -> float:
        """
        Get the total cost for a period.
        
        Args:
            period: The time period to check
            
        Returns:
            Total cost in USD
        """
        cutoff = datetime.now() - period
        total_cost = 0.0
        
        for record in self.records:
            if record.timestamp >= cutoff and record.success:
                total_cost += self._calculate_cost(
                    record.model_id,
                    record.input_tokens,
                    record.output_tokens
                )
        
        return total_cost
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of usage statistics.
        
        Returns:
            A dictionary with usage statistics
        """
        now = datetime.now()
        
        # Calculate time periods
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Filter records by time periods
        daily_records = [r for r in self.records if r.timestamp >= day_ago]
        weekly_records = [r for r in self.records if r.timestamp >= week_ago]
        monthly_records = [r for r in self.records if r.timestamp >= month_ago]
        
        # Calculate usage by model
        model_usage = {}
        for record in monthly_records:
            if record.model_id not in model_usage:
                model_usage[record.model_id] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                }
            
            model_usage[record.model_id]["requests"] += 1
            
            if record.success:
                model_usage[record.model_id]["input_tokens"] += record.input_tokens
                model_usage[record.model_id]["output_tokens"] += record.output_tokens
                model_usage[record.model_id]["cost"] += self._calculate_cost(
                    record.model_id,
                    record.input_tokens,
                    record.output_tokens
                )
        
        # Calculate success rates
        daily_success_rate = sum(1 for r in daily_records if r.success) / max(1, len(daily_records))
        weekly_success_rate = sum(1 for r in weekly_records if r.success) / max(1, len(weekly_records))
        monthly_success_rate = sum(1 for r in monthly_records if r.success) / max(1, len(monthly_records))
        
        # Calculate average latency
        daily_latency = sum(r.duration_ms for r in daily_records) / max(1, len(daily_records))
        weekly_latency = sum(r.duration_ms for r in weekly_records) / max(1, len(weekly_records))
        monthly_latency = sum(r.duration_ms for r in monthly_records) / max(1, len(monthly_records))
        
        return {
            "total_requests": len(self.records),
            "daily": {
                "requests": len(daily_records),
                "tokens": sum(r.input_tokens + r.output_tokens for r in daily_records if r.success),
                "cost": sum(self._calculate_cost(r.model_id, r.input_tokens, r.output_tokens) for r in daily_records if r.success),
                "success_rate": daily_success_rate,
                "avg_latency_ms": daily_latency
            },
            "weekly": {
                "requests": len(weekly_records),
                "tokens": sum(r.input_tokens + r.output_tokens for r in weekly_records if r.success),
                "cost": sum(self._calculate_cost(r.model_id, r.input_tokens, r.output_tokens) for r in weekly_records if r.success),
                "success_rate": weekly_success_rate,
                "avg_latency_ms": weekly_latency
            },
            "monthly": {
                "requests": len(monthly_records),
                "tokens": sum(r.input_tokens + r.output_tokens for r in monthly_records if r.success),
                "cost": sum(self._calculate_cost(r.model_id, r.input_tokens, r.output_tokens) for r in monthly_records if r.success),
                "success_rate": monthly_success_rate,
                "avg_latency_ms": monthly_latency
            },
            "by_model": model_usage,
            "quota_status": {
                "daily_tokens": {
                    "used": self.get_token_usage_for_period(timedelta(days=1)),
                    "limit": self.quota.daily_token_limit,
                    "percent": self.get_token_usage_for_period(timedelta(days=1)) / self.quota.daily_token_limit * 100
                },
                "hourly_requests": {
                    "used": self.get_request_count_for_period(timedelta(hours=1)),
                    "limit": self.quota.hourly_request_limit,
                    "percent": self.get_request_count_for_period(timedelta(hours=1)) / self.quota.hourly_request_limit * 100
                },
                "monthly_cost": {
                    "used": self.get_cost_for_period(timedelta(days=30)),
                    "limit": self.quota.monthly_cost_limit,
                    "percent": self.get_cost_for_period(timedelta(days=30)) / self.quota.monthly_cost_limit * 100
                }
            }
        }
    
    def _calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost for a request.
        
        Args:
            model_id: The model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        # Get the cost per 1k tokens for the model
        input_cost_per_1k = self.quota.cost_per_1k_input_tokens.get(
            model_id, self.quota.cost_per_1k_input_tokens["default"]
        )
        output_cost_per_1k = self.quota.cost_per_1k_output_tokens.get(
            model_id, self.quota.cost_per_1k_output_tokens["default"]
        )
        
        # Calculate the cost
        input_cost = input_tokens / 1000 * input_cost_per_1k
        output_cost = output_tokens / 1000 * output_cost_per_1k
        
        return input_cost + output_cost
    
    def _estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the cost for a request.
        
        Args:
            model_id: The model to use
            input_tokens: Estimated number of input tokens
            output_tokens: Estimated number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        return self._calculate_cost(model_id, input_tokens, output_tokens)
    
    async def _save_records(self):
        """Save usage records to disk."""
        if not self.storage_path:
            return
        
        try:
            # Create the directory if it doesn't exist
            storage_dir = Path(self.storage_path).parent
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert records to dictionaries
            records_data = [record.to_dict() for record in self.records]
            
            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(records_data, f, indent=2)
                
            logger.debug(f"Saved {len(self.records)} usage records to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving usage records: {e}")
    
    def _load_records(self):
        """Load usage records from disk."""
        if not self.storage_path:
            return
        
        try:
            # Check if the file exists
            storage_path = Path(self.storage_path)
            if not storage_path.exists():
                logger.debug(f"No usage records file found at {self.storage_path}")
                return
            
            # Read from file
            with open(self.storage_path, 'r') as f:
                records_data = json.load(f)
            
            # Convert dictionaries to records
            self.records = [UsageRecord.from_dict(data) for data in records_data]
            
            logger.debug(f"Loaded {len(self.records)} usage records from {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error loading usage records: {e}")
            self.records = []


# Create a global instance for convenience
default_tracker = UsageTracker(
    storage_path=get_config("tier3.usage_tracker.storage_path", "data/usage/bedrock_usage.json"),
    auto_save=get_config("tier3.usage_tracker.auto_save", True)
)


async def track_request(
    request_id: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    success: bool = True,
    error_type: Optional[str] = None,
    tracker: Optional[UsageTracker] = None
) -> UsageRecord:
    """
    Track an API request.
    
    Args:
        request_id: The ID of the request
        model_id: The model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        duration_ms: Duration of the API call in milliseconds
        success: Whether the API call was successful
        error_type: Type of error if the call failed
        tracker: The usage tracker to use (defaults to the global instance)
        
    Returns:
        The created usage record
    """
    tracker = tracker or default_tracker
    return await tracker.track_usage(
        request_id=request_id,
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        success=success,
        error_type=error_type
    )


async def check_quota(
    model_id: str,
    estimated_tokens: int,
    tracker: Optional[UsageTracker] = None
) -> Tuple[bool, str]:
    """
    Check if a request would exceed the quota.
    
    Args:
        model_id: The model to use
        estimated_tokens: Estimated number of tokens for the request
        tracker: The usage tracker to use (defaults to the global instance)
        
    Returns:
        A tuple of (allowed, reason)
    """
    tracker = tracker or default_tracker
    return await tracker.check_quota(model_id, estimated_tokens)


def get_usage_summary(tracker: Optional[UsageTracker] = None) -> Dict[str, Any]:
    """
    Get a summary of usage statistics.
    
    Args:
        tracker: The usage tracker to use (defaults to the global instance)
        
    Returns:
        A dictionary with usage statistics
    """
    tracker = tracker or default_tracker
    return tracker.get_usage_summary() 