"""
Retry Utilities

This module provides utilities for retrying operations with configurable
backoff strategies, jitter, and retry conditions.
"""

import asyncio
import logging
import random
import time
from typing import Callable, TypeVar, Optional, List, Dict, Any, Union, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Return type of the function being retried


class RetryConfig:
    """
    Configuration for retry behavior.
    
    This class defines how retries should be performed, including the maximum
    number of retries, the delay between retries, and whether to use jitter.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.25,
        retry_exceptions: Optional[List[Type[Exception]]] = None,
        retry_on: Optional[Callable[[Exception], bool]] = None
    ):
        """
        Initialize the retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Factor by which the delay increases after each retry
            jitter: Whether to add randomness to the delay
            jitter_factor: Factor by which to vary the delay (0.25 = ±25%)
            retry_exceptions: List of exception types to retry on
            retry_on: Function that takes an exception and returns True if it should be retried
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.retry_exceptions = retry_exceptions or []
        self.retry_on = retry_on
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            exception: The exception that was raised
            attempt: The current attempt number (0-based)
            
        Returns:
            True if a retry should be attempted, False otherwise
        """
        # Check if we've exceeded the maximum number of retries
        if attempt >= self.max_retries:
            return False
        
        # Check if the exception is in the list of retryable exceptions
        if self.retry_exceptions and not any(isinstance(exception, exc_type) for exc_type in self.retry_exceptions):
            return False
        
        # Check if the retry_on function returns True
        if self.retry_on and not self.retry_on(exception):
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next retry.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            The delay in seconds
        """
        # Calculate the base delay using exponential backoff
        delay = self.base_delay * (self.backoff_factor ** attempt)
        
        # Cap the delay at the maximum
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)
            
            # Ensure the delay is not negative
            delay = max(delay, 0.001)
        
        return delay


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any
) -> Any:
    """
    Retry an async function with the specified configuration.
    
    Args:
        func: The async function to retry
        *args: Positional arguments to pass to the function
        config: The retry configuration
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        The last exception raised by the function if all retries fail
    """
    config = config or RetryConfig()
    attempt = 0
    last_exception = None
    
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if not config.should_retry(e, attempt):
                logger.warning(f"Retry failed after {attempt + 1} attempts: {str(e)}")
                raise
            
            delay = config.get_delay(attempt)
            logger.info(f"Retry attempt {attempt + 1}/{config.max_retries} after {delay:.2f}s: {str(e)}")
            
            await asyncio.sleep(delay)
            attempt += 1


def retry_sync(
    func: Callable[..., Any],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any
) -> Any:
    """
    Retry a synchronous function with the specified configuration.
    
    Args:
        func: The function to retry
        *args: Positional arguments to pass to the function
        config: The retry configuration
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        The last exception raised by the function if all retries fail
    """
    config = config or RetryConfig()
    attempt = 0
    last_exception = None
    
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if not config.should_retry(e, attempt):
                logger.warning(f"Retry failed after {attempt + 1} attempts: {str(e)}")
                raise
            
            delay = config.get_delay(attempt)
            logger.info(f"Retry attempt {attempt + 1}/{config.max_retries} after {delay:.2f}s: {str(e)}")
            
            time.sleep(delay)
            attempt += 1


def retry_async_decorator(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions.
    
    Args:
        config: The retry configuration
        
    Returns:
        A decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


def retry_sync_decorator(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying synchronous functions.
    
    Args:
        config: The retry configuration
        
    Returns:
        A decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_sync(func, *args, config=config, **kwargs)
        return wrapper
    return decorator 