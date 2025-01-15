"""Data models for the application using Pydantic for validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class Rule(BaseModel):
    """Model for a single rule with validation."""
    content: str = Field(..., min_length=1, description="The content of the rule")
    
    @validator('content')
    def content_not_empty(cls, v: str) -> str:
        """Validate that content is not just whitespace."""
        if v.strip() == "":
            raise ValueError("Rule content cannot be empty or just whitespace")
        return v

class IgnorePatterns(BaseModel):
    """Model for ignore patterns."""
    directories: List[str] = Field(
        default_factory=lambda: [
            "__pycache__", ".git", "node_modules", 
            "venv", ".venv", "env", ".env",
            "build", "dist", ".pytest_cache", "target"
        ],
        description="List of directory patterns to ignore"
    )
    files: List[str] = Field(
        default_factory=lambda: [
            "*.pyc", "*.pyo", "*.pyd",
            ".DS_Store", "Thumbs.db",
            "*.log", "*.sqlite", "*.db",
            # Binary files
            "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp",
            "*.mp3", "*.mp4", "*.avi", "*.mov",
            "*.zip", "*.tar", "*.gz", "*.7z",
            "*.exe", "*.dll", "*.so", "*.dylib"
        ],
        description="List of file patterns to ignore"
    )

class Settings(BaseModel):
    """Model for application settings with validation."""
    saved_rules: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of rule name to rule content"
    )
    path: str = Field(
        default="",
        description="Path to the repository"
    )
    use_relative_paths: bool = Field(
        default=True,
        description="Use relative paths in file references"
    )
    model: str = Field(
        default="gpt-4",
        description="Model to use for token analysis"
    )
    ignore_patterns: IgnorePatterns = Field(
        default_factory=IgnorePatterns,
        description="Patterns to ignore when scanning repository"
    )
    
    @validator('saved_rules')
    def validate_rules(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate each rule in the rules dictionary."""
        for name, content in v.items():
            if not name or name.strip() == "":
                raise ValueError("Rule name cannot be empty")
            if not content or content.strip() == "":
                raise ValueError(f"Content for rule '{name}' cannot be empty")
        return v

class UserSettings(BaseModel):
    """Model for user-specific settings with validation."""
    settings: Settings = Field(
        default_factory=Settings,
        description="User settings including rules"
    )
    config_path: Optional[str] = Field(
        None,
        description="Path to the config file"
    )
