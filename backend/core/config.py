"""Configuration management module."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'path': str(Path.cwd()),
    'ignore_patterns': {
        'directories': [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            '.venv',
            'env',
            '.env',
            'build',
            'dist',
            '.pytest_cache',
            'target'
        ],
        'files': [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db',
            '*.log',
            '*.sqlite',
            '*.db'
        ]
    },
    'max_file_size': 1024 * 1024,  # 1MB
    'max_files': 1000,
    'excluded_extensions': [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.mp3', '.mp4', '.avi', '.mov',
        '.zip', '.tar', '.gz', '.7z',
        '.exe', '.dll', '.so', '.dylib'
    ]
}

CONFIG_FILE = 'config/config.yaml'

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    try:
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return {**DEFAULT_CONFIG, **(config or {})}
        else:
            logger.info("No config file found, using defaults, tried in path: %s", config_path)
            return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config.yaml."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.safe_dump(config, f)
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return False

def update_config(updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update configuration with new values."""
    try:
        config = load_config()
        config.update(updates)
        if save_config(config):
            return config
        return None
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return None
