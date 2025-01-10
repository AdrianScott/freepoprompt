from typing import Optional, Union
import logging
from pathlib import Path
from .path_utils import sanitize_path, validate_path

class FileHandler:
    """Handles file operations with proper error handling and security validation."""

    def __init__(self, root_path: Optional[Union[str, Path]] = None, allow_writes: bool = False):
        """
        Initialize the file handler.

        Args:
            root_path: Optional root path to restrict file operations to
            allow_writes: If True, allows actual file creation/modification. If False, only simulates writes
        """
        self.logger = logging.getLogger(__name__)
        self.root_path = Path(root_path) if root_path else None
        self.allow_writes = False # If True, allows actual file creation/modification. If False, only simulates writes. Default is False for security reasons. allow_writes

    def read_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Safely read file contents with path validation.

        Args:
            file_path: Path to the file

        Returns:
            File contents as string or None if error occurs
        """
        try:
            # Validate path before operations
            if not validate_path(file_path, self.root_path):
                self.logger.error(f"Invalid or unsafe path: {file_path}")
                return None

            path = sanitize_path(file_path)
            self.logger.debug(f"Reading file: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.debug(f"Successfully read {len(content)} bytes from {path}")
                return content
        except UnicodeDecodeError:
            self.logger.error(f"Failed to decode file: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return None

    def write_file(self, file_path: Union[str, Path], content: str) -> bool:
        """
        Safely write content to file with path validation.
        If allow_writes is False, only simulates the write operation and logs what would happen.

        Args:
            file_path: Path to the file
            content: Content to write

        Returns:
            True if successful (or would be successful), False otherwise
        """
        try:
            path = sanitize_path(file_path)

            # Validate parent directory is safe before creating
            parent = path.parent
            if self.root_path and not validate_path(parent, self.root_path, allow_nonexistent=True):
                self.logger.error(f"Invalid or unsafe parent directory: {parent}")
                return False

            # Check if this would be a new file
            is_new_file = not path.exists()

            if not self.allow_writes:
                # Simulate the operation and log what would happen
                action = "created" if is_new_file else "modified"
                self.logger.info(f"SIMULATION: Read-only: File would have been {action}: {path}")
                if not parent.exists():
                    self.logger.info(f"SIMULATION: Read-only: Directory structure would have been created: {parent}")
                self.logger.info(f"SIMULATION: Read-only: Would have written {len(content)} bytes to {path}")
                return True

            # Actually perform the write operation
            if not parent.exists():
                self.logger.info(f"Creating directory structure: {parent}")
                parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Successfully created directory structure: {parent}")

            # Final validation before write
            if not validate_path(path, self.root_path, allow_nonexistent=True):
                self.logger.error(f"Path validation failed after directory creation: {path}")
                return False

            self.logger.info(f"Writing {len(content)} bytes to file: {path}")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            action = "Created" if is_new_file else "Modified"
            self.logger.info(f"Successfully {action.lower()} file: {path}")
            return True

        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {str(e)}")
            return False