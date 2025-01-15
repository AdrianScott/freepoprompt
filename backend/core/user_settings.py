"""User settings management module."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from platformdirs import user_config_dir

from .models import Settings, UserSettings, Rule

logger = logging.getLogger(__name__)

def get_user_settings_path() -> Path:
    """Get user-specific settings path using platformdirs."""
    config_dir = Path(user_config_dir("freepoprompt", appauthor=False, roaming=True))
    settings_path = config_dir / 'settings.yaml'
    logger.info(f"Settings path resolved to: {settings_path} (absolute: {settings_path.absolute()})")
    return settings_path

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
        logger.info(f"Loading settings from: {settings_path}")
        if settings_path.exists():
            with settings_path.open('r', encoding='utf-8') as f:
                # Use safe_load for security
                raw_settings = yaml.safe_load(f) or {}
                # Validate settings through pydantic
                settings = Settings(**raw_settings)
                logger.info(f"Loaded and validated settings: {settings.dict()}")
                return settings.dict()
        logger.info("Settings file does not exist, returning empty dict")
        return Settings().dict()
    except Exception as e:
        logger.error(f"Error loading user settings: {str(e)}", exc_info=True)
        return Settings().dict()

def save_user_settings(settings: Dict[str, Any]) -> bool:
    """Save user-specific settings with validation."""
    try:
        # Validate settings through pydantic
        validated_settings = Settings(**settings)
        settings_path = get_user_settings_path()
        logger.info(f"Saving validated settings to: {settings_path}")
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write settings with explicit encoding
        with settings_path.open('w', encoding='utf-8') as f:
            yaml.dump(validated_settings.dict(), f, allow_unicode=True)
        
        # Verify the save
        if settings_path.exists():
            with settings_path.open('r', encoding='utf-8') as f:
                saved_content = yaml.safe_load(f)
                # Validate saved content
                saved_settings = Settings(**saved_content)
                if saved_settings.dict() == validated_settings.dict():
                    logger.info("Settings saved and verified successfully")
                    return True
                else:
                    logger.error("Settings verification failed - content mismatch")
                    return False
        else:
            logger.error("Settings file not found after save")
            return False
            
    except Exception as e:
        logger.error(f"Error saving user settings: {str(e)}", exc_info=True)
        return False

def get_effective_settings() -> Dict[str, Any]:
    """Get effective settings (defaults + user settings)."""
    defaults = load_defaults()
    user_settings = load_user_settings()
    
    logger.info(f"Loading defaults: {defaults}")
    logger.info(f"Loading user settings: {user_settings}")
    
    # Merge settings
    effective = defaults.copy()
    effective.update(user_settings)
    
    logger.info(f"Effective settings: {effective}")
    
    # Validate final settings
    if 'path' in effective:
        path = effective['path']
        if path and not isinstance(path, str):
            logger.error(f"Path must be string, got {type(path)}")
            effective['path'] = str(path)
        logger.info(f"Using repository path: {effective.get('path')}")
    else:
        logger.warning("No path found in settings")
    
    return effective
