"""User settings management module."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from platformdirs import user_config_dir

logger = logging.getLogger(__name__)

def get_user_settings_path() -> Path:
    """Get user-specific settings path using platformdirs."""
    config_dir = Path(user_config_dir("freepoprompt", appauthor=False, roaming=True))
    return config_dir / 'settings.yaml'

def get_app_dir() -> Path:
    """Get the application's base directory."""
    return Path(__file__).parent.parent.parent.resolve()

def load_defaults() -> Dict[str, Any]:
    """Load read-only app defaults."""
    try:
        defaults_path = get_app_dir() / 'config' / 'defaults.yaml'
        if not defaults_path.exists():
            logger.error(f"Defaults file not found at: {defaults_path}")
            return {}
        with defaults_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading defaults: {str(e)}")
        return {}

def load_user_settings() -> Dict[str, Any]:
    """Load user-specific settings, create if not exists."""
    try:
        settings_path = get_user_settings_path()
        if settings_path.exists():
            with settings_path.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    except Exception as e:
        logger.error(f"Error loading user settings: {str(e)}")
        return {}

def save_user_settings(settings: Dict[str, Any]) -> bool:
    """Save user-specific settings."""
    try:
        settings_path = get_user_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write settings with explicit encoding
        with settings_path.open('w', encoding='utf-8') as f:
            yaml.dump(settings, f, allow_unicode=True)
        
        logger.info(f"User settings saved successfully to {settings_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving user settings: {str(e)}")
        return False

def get_effective_settings() -> Dict[str, Any]:
    """Get effective settings (defaults + user settings)."""
    defaults = load_defaults()
    user_settings = load_user_settings()
    return {**defaults, **user_settings}
