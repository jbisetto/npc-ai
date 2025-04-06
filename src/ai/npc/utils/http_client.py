"""
HTTP Client Utilities

This module provides utilities for making HTTP requests to external services.
"""

import httpx
import json
from typing import Dict, Any, Optional


async def make_api_request(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, 
                          headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Make an HTTP request to an external API.
    
    Args:
        url: The URL to make the request to
        method: The HTTP method to use (GET, POST, etc.)
        data: The data to send with the request (for POST, PUT, etc.)
        headers: The headers to send with the request
        timeout: The timeout in seconds
        
    Returns:
        The JSON response from the API as a dictionary
        
    Raises:
        httpx.HTTPError: If the request fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    headers = headers or {}
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = await client.post(url, json=data, headers=headers, timeout=timeout)
        elif method.upper() == "PUT":
            response = await client.put(url, json=data, headers=headers, timeout=timeout)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    response.raise_for_status()
    return response.json() 