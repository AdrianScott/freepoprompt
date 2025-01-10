"""Handles repository traversal and file analysis with security validation."""

from typing import Dict, List, Tuple, Optional, Any, Union
import os
import logging
import fnmatch
import yaml
from pathlib import Path
from datetime import datetime
from .path_utils import sanitize_path, validate_path, secure_join

# Just get the logger, don't configure it
logger = logging.getLogger(__name__)

class RepositoryCrawler:
    """Handles repository traversal and file analysis with security validation."""
    
    def __init__(self, root_path: Union[str, Path], config: Dict[str, Any]):
        """Initialize the repository crawler."""
        try:
            # Validate and sanitize root path
            self.root_path = sanitize_path(root_path)
            if not validate_path(self.root_path, allow_nonexistent=True):
                raise ValueError(f"Invalid or unsafe root path: {root_path}")
                
            # Deep copy config to prevent reference issues
            self.config = {
                'ignore_patterns': {
                    'directories': list(config.get('ignore_patterns', {}).get('directories', [])),
                    'files': list(config.get('ignore_patterns', {}).get('files', []))
                },
                'excluded_extensions': list(config.get('excluded_extensions', []))
            }
            
            # Cache for file tree to prevent unnecessary recalculation
            self._file_tree_cache = None
            self._config_hash = None
            
            logger.info("Starting Repository Crawler")
            logger.debug(f"Initialized with root: {root_path}")
            logger.debug(f"Config: {self.config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize crawler: {str(e)}")
            raise
            
    def _get_config_hash(self) -> str:
        """Get a more reliable hash of current config for cache invalidation."""
        try:
            # Sort lists to ensure consistent hashing
            sorted_config = {
                'ignore_patterns': {
                    'directories': sorted(self.config['ignore_patterns']['directories']),
                    'files': sorted(self.config['ignore_patterns']['files'])
                },
                'excluded_extensions': sorted(self.config['excluded_extensions'])
            }
            # Use stable string representation
            config_str = f"dirs:{','.join(sorted_config['ignore_patterns']['directories'])}|files:{','.join(sorted_config['ignore_patterns']['files'])}|exts:{','.join(sorted_config['excluded_extensions'])}"
            return str(hash(config_str))
        except Exception as e:
            logger.error(f"Error calculating config hash: {str(e)}")
            # Return unique hash to invalidate cache
            return str(hash(str(datetime.now())))
            
    def _invalidate_cache(self):
        """Safely invalidate the file tree cache."""
        self._file_tree_cache = None
        self._config_hash = None
        
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update crawler configuration with validation and proper cache management."""
        try:
            # Validate new config structure
            if not isinstance(new_config.get('ignore_patterns'), dict):
                logger.error("Invalid ignore_patterns structure in new config")
                return False
                
            # Extract and validate patterns
            new_dirs = list(new_config.get('ignore_patterns', {}).get('directories', []))
            new_files = list(new_config.get('ignore_patterns', {}).get('files', []))
            new_exts = list(new_config.get('excluded_extensions', []))
            
            if not all(isinstance(p, str) for p in new_dirs + new_files + new_exts):
                logger.error("Invalid pattern type found - all patterns must be strings")
                return False
                
            # Update with validated data
            self.config = {
                'ignore_patterns': {
                    'directories': new_dirs,
                    'files': new_files
                },
                'excluded_extensions': new_exts
            }
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info("Configuration updated successfully")
            logger.debug(f"New config: {self.config}")
            return True
            
        except Exception as e:
            logger.exception("Error updating configuration")
            return False
            
    def _is_ignored(self, path: Union[str, Path], is_dir: bool = False) -> bool:
        """Check if a path should be ignored based on configured patterns."""
        try:
            path_str = str(Path(path).name)  # Only check the filename/dirname
            
            # Directory check
            if is_dir:
                patterns = self.config['ignore_patterns']['directories']
                return any(fnmatch.fnmatch(path_str, pattern) for pattern in patterns)
            
            # File check
            patterns = self.config['ignore_patterns']['files']
            if any(fnmatch.fnmatch(path_str, pattern) for pattern in patterns):
                return True
                
            # Extension check
            extension = Path(path_str).suffix.lower()
            if extension in self.config['excluded_extensions']:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking ignore status: {str(e)}")
            return True  # Ignore on error for safety
            
    def get_file_tree(self) -> Dict:
        """Generate a hierarchical file tree structure with improved caching and security."""
        try:
            current_hash = self._get_config_hash()
            
            # Return cached tree if config hasn't changed
            if (self._file_tree_cache is not None and 
                self._config_hash is not None and 
                self._config_hash == current_hash):
                return self._file_tree_cache
                
            # Validate root path again before scanning
            if not validate_path(self.root_path, allow_nonexistent=True):
                raise ValueError(f"Invalid or unsafe root path: {self.root_path}")
                
            tree = {'path': str(self.root_path), 'type': 'directory', 'children': []}
            
            for root, dirs, files in os.walk(str(self.root_path)):
                logger.debug(f"Processing directory: {root}")
                logger.debug(f"Found directories: {dirs}")
                logger.debug(f"Found files: {files}")
                
                # Validate each directory being processed
                if not validate_path(root, self.root_path, allow_nonexistent=True):
                    logger.warning(f"Skipping invalid directory: {root}")
                    continue
                    
                current_node = self._get_node_at_path(tree, root)
                if not current_node:
                    logger.warning(f"Could not find node for path: {root}")
                    continue
                    
                # Process directories
                dirs[:] = [d for d in dirs if not self._is_ignored(d, True)]
                logger.debug(f"After filtering, directories: {dirs}")
                for dirname in dirs:
                    dir_path = secure_join(root, dirname)
                    if validate_path(dir_path, self.root_path, allow_nonexistent=True):
                        current_node['children'].append({
                            'path': str(dir_path),
                            'type': 'directory',
                            'children': []
                        })
                        
                # Process files
                filtered_files = [f for f in files if not self._is_ignored(f)]
                logger.debug(f"After filtering, files: {filtered_files}")
                for filename in filtered_files:
                    file_path = secure_join(root, filename)
                    if validate_path(file_path, self.root_path, allow_nonexistent=True):
                        current_node['children'].append({
                            'path': str(file_path),
                            'type': 'file'
                        })
                        
            logger.debug(f"Final tree: {tree}")
            self._file_tree_cache = tree
            self._config_hash = current_hash
            return tree
            
        except Exception as e:
            logger.error(f"Error generating file tree: {str(e)}")
            raise
            
    def _get_node_at_path(self, tree: Dict, path: str) -> Optional[Dict]:
        """Find a node in the tree by its path."""
        try:
            # If this is the root path, return the root node
            if path == str(self.root_path):
                return tree
            
            # Get the relative path from root
            rel_path = Path(path).relative_to(self.root_path)
            current_node = tree
            
            # For each part of the path, find the matching child
            for part in rel_path.parts:
                found = False
                for child in current_node['children']:
                    if Path(child['path']).name == part:
                        current_node = child
                        found = True
                        break
                if not found:
                    return None
                    
            return current_node
            
        except Exception as e:
            logger.error(f"Error finding node at path: {str(e)}")
            return None
            
    def walk(self) -> List[Tuple[str, int]]:
        """
        Walk through the repository and collect file information.
        
        Returns:
            List of tuples containing (file_path, size_in_bytes)
        """
        logger.info("Walking repository for file information")
        files_info = []
        
        try:
            for root, dirs, files in os.walk(self.root_path):
                # Remove ignored directories in-place
                dirs[:] = [d for d in dirs if not self._is_ignored(d, True)]
                
                # Process files
                for filename in files:
                    if self._is_ignored(filename):
                        continue
                        
                    file_path = secure_join(root, filename)
                    if validate_path(file_path, self.root_path):
                        try:
                            size = os.path.getsize(file_path)
                            files_info.append((str(file_path), size))
                        except OSError as e:
                            logger.warning(f"Could not get size for {file_path}: {e}")
                            
            return files_info
            
        except Exception as e:
            logger.error(f"Error walking repository: {str(e)}")
            raise