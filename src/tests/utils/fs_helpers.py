"""
File system helpers for testing.

This module provides utilities for working with files during testing,
including temporary file creation and cleanup.
"""

import os
import json
import shutil
from typing import Dict, Any, Optional
from pathlib import Path


def create_temp_json_file(
    data: Dict[str, Any],
    directory: Optional[Path] = None,
    filename: Optional[str] = None
) -> Path:
    """
    Create a temporary JSON file with the given data.
    
    Args:
        data: The data to write to the file
        directory: Optional directory to create the file in
        filename: Optional filename to use
        
    Returns:
        Path to the created file
    """
    if directory is None:
        directory = Path.cwd() / "test_data"
    
    if filename is None:
        filename = "test_data.json"
        
    # Ensure directory exists
    directory.mkdir(parents=True, exist_ok=True)
    
    file_path = directory / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return file_path


def create_corrupted_json_file(
    directory: Optional[Path] = None,
    filename: Optional[str] = None,
    partial_data: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Create a corrupted JSON file for testing error handling.
    
    Args:
        directory: Optional directory to create the file in
        filename: Optional filename to use
        partial_data: Optional partial data to include before corruption
        
    Returns:
        Path to the created file
    """
    if directory is None:
        directory = Path.cwd() / "test_data"
    
    if filename is None:
        filename = "corrupted_data.json"
        
    # Ensure directory exists
    directory.mkdir(parents=True, exist_ok=True)
    
    file_path = directory / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        if partial_data:
            # Write partial valid JSON then corrupt it
            f.write(json.dumps(partial_data, indent=2)[:-5])
        else:
            # Write invalid JSON
            f.write('{"invalid": "json", missing: }')
        
    return file_path


def cleanup_test_files(
    directory: Optional[Path] = None,
    pattern: str = "test_*.json"
) -> None:
    """
    Clean up test files matching the pattern.
    
    Args:
        directory: Optional directory to clean up
        pattern: Glob pattern for files to remove
    """
    if directory is None:
        directory = Path.cwd() / "test_data"
        
    if directory.exists():
        for file_path in directory.glob(pattern):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {file_path}: {e}")
        
        # Try to remove directory if empty
        try:
            directory.rmdir()
        except Exception:
            pass  # Directory not empty or other error 