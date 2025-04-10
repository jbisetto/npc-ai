"""
Monitoring Utilities

This module provides utilities for monitoring the performance and behavior
of the companion AI system, particularly focusing on tracking metrics related
to fallback mechanisms and error handling.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Counter as CounterType
from collections import Counter, defaultdict
import threading
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProcessorMonitor:
    """
    Monitor for tracking processor performance and behavior.
    
    This class provides methods for tracking metrics related to the processor's
    performance, including request counts, error counts, and
    fallback counts. It also provides methods for generating reports and
    persisting metrics to disk.

    TODO(cleanup): This monitoring system is currently not being actively used.
    While it's instantiated in HostedProcessor, none of its tracking methods
    are called. Its intended functionality is currently being handled by:
    - Logger (error tracking)
    - UsageTracker (API usage)
    - Direct logging in HostedProcessor (response times)
    - ConversationManager (success/failure tracking)
    
    Need to determine if this should be:
    1. Properly integrated to provide additional metrics
    2. Removed as redundant functionality
    3. Refactored to complement existing monitoring
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Create a new instance of the monitor if one doesn't exist."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProcessorMonitor, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """Initialize the monitor."""
        self.reset()
        self._start_time = datetime.now()
        self._metrics_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'metrics')
        os.makedirs(self._metrics_dir, exist_ok=True)
    
    def reset(self):
        """Reset all metrics."""
        self._metrics = {
            'requests': Counter(),
            'errors': Counter(),
            'fallbacks': Counter(),
            'response_times': defaultdict(list),
            'success_counts': Counter(),  # Count of successful responses
            'last_errors': defaultdict(list)
        }
    
    def track_request(self, processor_name: str, request_id: str):
        """
        Track a request to a processor.
        
        Args:
            processor_name: The name of the processor (e.g., 'tier1', 'tier2')
            request_id: The ID of the request
        """
        with self._lock:
            self._metrics['requests'][processor_name] += 1
            logger.debug(f"Tracked request to {processor_name}: {request_id}")
    
    def track_error(self, processor_name: str, error_type: str, error_message: str):
        """
        Track an error from a processor.
        
        Args:
            processor_name: The name of the processor (e.g., 'tier1', 'tier2')
            error_type: The type of error (e.g., 'connection_error', 'model_error')
            error_message: The error message
        """
        with self._lock:
            error_key = f"{processor_name}:{error_type}"
            self._metrics['errors'][error_key] += 1
            
            # Keep track of the last 10 errors of each type
            errors = self._metrics['last_errors'][error_key]
            errors.append({
                'timestamp': datetime.now().isoformat(),
                'message': error_message
            })
            self._metrics['last_errors'][error_key] = errors[-10:]  # Keep only the last 10
            
            logger.debug(f"Tracked error from {processor_name}: {error_type} - {error_message}")
    
    def track_fallback(self, processor_name: str, fallback_type: str):
        """
        Track a fallback from a processor.
        
        Args:
            processor_name: The name of the processor (e.g., 'tier1', 'tier2')
            fallback_type: The type of fallback (e.g., 'simpler_model', 'tier1')
        """
        with self._lock:
            fallback_key = f"{processor_name}:{fallback_type}"
            self._metrics['fallbacks'][fallback_key] += 1
            logger.debug(f"Tracked fallback from {processor_name}: {fallback_type}")
    
    def track_response_time(self, processor_name: str, response_time_ms: float):
        """
        Track the response time of a processor.
        
        Args:
            processor_name: The name of the processor (e.g., 'tier1', 'tier2')
            response_time_ms: The response time in milliseconds
        """
        with self._lock:
            self._metrics['response_times'][processor_name].append(response_time_ms)
            logger.debug(f"Tracked response time from {processor_name}: {response_time_ms}ms")
    
    def track_success(self, processor_name: str, is_success: bool):
        """
        Track a successful or failed response from a processor.
        
        Args:
            processor_name: The name of the processor (e.g., 'tier1', 'tier2')
            is_success: Whether the response was successful
        """
        with self._lock:
            # Increment the success count if the response was successful
            if is_success:
                self._metrics['success_counts'][processor_name] += 1
            
            logger.debug(f"Tracked {'successful' if is_success else 'failed'} response from {processor_name}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current metrics.
        
        Returns:
            A dictionary of metrics
        """
        with self._lock:
            # Calculate derived metrics
            metrics = {
                'requests': dict(self._metrics['requests']),
                'errors': dict(self._metrics['errors']),
                'fallbacks': dict(self._metrics['fallbacks']),
                'success_counts': dict(self._metrics['success_counts']),
                'last_errors': dict(self._metrics['last_errors']),
                'uptime_seconds': (datetime.now() - self._start_time).total_seconds()
            }
            
            # Calculate success rates
            success_rates = {}
            for processor, count in metrics['requests'].items():
                if count > 0:
                    success_count = metrics['success_counts'].get(processor, 0)
                    success_rates[processor] = success_count / count
                else:
                    success_rates[processor] = 0.0
            
            metrics['success_rate'] = success_rates
            
            # Calculate average response times
            avg_response_times = {}
            for processor, times in self._metrics['response_times'].items():
                if times:
                    avg_response_times[processor] = sum(times) / len(times)
                    
                    # Only calculate percentiles if we have enough data
                    if len(times) >= 10:
                        # Also include p95 and p99 response times
                        times_sorted = sorted(times)
                        p95_index = int(len(times) * 0.95)
                        p99_index = int(len(times) * 0.99)
                        avg_response_times[f"{processor}_p95"] = times_sorted[p95_index] if p95_index < len(times) else times_sorted[-1]
                        avg_response_times[f"{processor}_p99"] = times_sorted[p99_index] if p99_index < len(times) else times_sorted[-1]
            
            metrics['avg_response_time_ms'] = avg_response_times
            
            return metrics
    
    def save_metrics(self):
        """Save the current metrics to disk."""
        # Get metrics with a timeout to avoid deadlocks
        try:
            # Try to acquire the lock with a timeout
            if not self._lock.acquire(timeout=1.0):
                logger.warning("Could not acquire lock for saving metrics, skipping")
                return
                
            try:
                # Calculate metrics while holding the lock
                metrics = {
                    'requests': dict(self._metrics['requests']),
                    'errors': dict(self._metrics['errors']),
                    'fallbacks': dict(self._metrics['fallbacks']),
                    'success_counts': dict(self._metrics['success_counts']),
                    'last_errors': dict(self._metrics['last_errors']),
                    'uptime_seconds': (datetime.now() - self._start_time).total_seconds()
                }
                
                # Calculate success rates
                success_rates = {}
                for processor, count in metrics['requests'].items():
                    if count > 0:
                        success_count = metrics['success_counts'].get(processor, 0)
                        success_rates[processor] = success_count / count
                    else:
                        success_rates[processor] = 0.0
                
                metrics['success_rate'] = success_rates
                
                # Calculate average response times
                avg_response_times = {}
                for processor, times in self._metrics['response_times'].items():
                    if times:
                        avg_response_times[processor] = sum(times) / len(times)
                        
                        # Only calculate percentiles if we have enough data
                        if len(times) >= 10:
                            # Also include p95 and p99 response times
                            times_sorted = sorted(times)
                            p95_index = int(len(times) * 0.95)
                            p99_index = int(len(times) * 0.99)
                            avg_response_times[f"{processor}_p95"] = times_sorted[p95_index] if p95_index < len(times) else times_sorted[-1]
                            avg_response_times[f"{processor}_p99"] = times_sorted[p99_index] if p99_index < len(times) else times_sorted[-1]
                
                metrics['avg_response_time_ms'] = avg_response_times
                
                # Write to disk
                file_path = os.path.join(self._metrics_dir, f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(file_path, 'w') as f:
                    json.dump(metrics, f, indent=2, default=str)
                
                logger.info(f"Saved metrics to {file_path}")
            finally:
                self._lock.release()
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}", exc_info=True)
    
    def log_metrics_summary(self):
        """Log a summary of the current metrics."""
        try:
            metrics = self.get_metrics()
            
            logger.info("=== Metrics Summary ===")
            logger.info(f"Uptime: {timedelta(seconds=int(metrics['uptime_seconds']))}")
            
            logger.info("Requests:")
            for processor, count in metrics['requests'].items():
                success_rate = metrics['success_rate'].get(processor, 0.0)
                logger.info(f"  {processor}: {count} requests, {success_rate:.2%} success rate")
            
            logger.info("Errors:")
            for error, count in metrics['errors'].items():
                logger.info(f"  {error}: {count}")
            
            logger.info("Fallbacks:")
            for fallback, count in metrics['fallbacks'].items():
                logger.info(f"  {fallback}: {count}")
            
            logger.info("Average Response Times (ms):")
            for processor, time_ms in metrics.get('avg_response_time_ms', {}).items():
                if not processor.endswith('_p95') and not processor.endswith('_p99'):
                    p95 = metrics.get('avg_response_time_ms', {}).get(f"{processor}_p95", 'N/A')
                    p99 = metrics.get('avg_response_time_ms', {}).get(f"{processor}_p99", 'N/A')
                    logger.info(f"  {processor}: avg={time_ms:.2f}ms, p95={p95 if isinstance(p95, str) else f'{p95:.2f}ms'}, p99={p99 if isinstance(p99, str) else f'{p99:.2f}ms'}")
                    
            logger.info("======================")
        except Exception as e:
            logger.error(f"Error logging metrics summary: {e}", exc_info=True) 