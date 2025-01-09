"""Utilities for secure path handling and validation."""

import os
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def sanitize_path(file_path: Union[str, Path]) -> Path:
    """
    Sanitize a file path by resolving and normalizing it.
    
    Args:
        file_path: The path to sanitize
        
    Returns:
        Path: A sanitized Path object
    """
    try:
        return Path(file_path).resolve()
    except Exception as e:
        logger.error(f"Error sanitizing path {file_path}: {str(e)}")
        raise ValueError(f"Invalid path: {file_path}")

def validate_path(file_path: Union[str, Path], root_path: Optional[Union[str, Path]] = None, allow_nonexistent: bool = False) -> bool:
    """
    Validate a file path for security.
    
    Args:
        file_path: The path to validate
        root_path: Optional root path to ensure file_path doesn't escape from
        allow_nonexistent: If True, allows paths that don't exist yet (for file/directory creation)
        
    Returns:
        bool: True if path is valid and safe, False otherwise
    """
    try:
        path = sanitize_path(file_path)
        
        # Check existence only if we're not allowing nonexistent paths
        if not allow_nonexistent and not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return False
                
        if path.is_symlink():
            logger.warning(f"Path is a symlink (not allowed): {path}")
            return False
            
        # If root_path is provided, ensure path doesn't escape it
        if root_path:
            root = sanitize_path(root_path)
            try:
                # For new files/dirs, check if their parent is within root
                check_path = path.parent if allow_nonexistent and not path.exists() else path
                check_path.relative_to(root)
            except ValueError:
                logger.warning(f"Path {path} is outside root {root}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error validating path {file_path}: {str(e)}")
        return False

def secure_join(base: Union[str, Path], *paths: str) -> Path:
    """
    Securely join path components.
    
    Args:
        base: The base path
        *paths: Additional path components
        
    Returns:
        Path: A sanitized joined path
    """
    try:
        base_path = sanitize_path(base)
        result = base_path.joinpath(*paths)
        return result.resolve()
    except Exception as e:
        logger.error(f"Error joining paths {base} and {paths}: {str(e)}")
        raise ValueError(f"Invalid path components: {base}, {paths}")
