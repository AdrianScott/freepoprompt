"""Component for viewing file contents."""

import streamlit as st
from pathlib import Path
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler

logger = logging.getLogger(__name__)

class FileViewer:
    """Component for viewing and interacting with file contents."""
    
    def __init__(self, file_path: str, root_path: str):
        """Initialize the file viewer."""
        self.file_path = Path(file_path)
        self.root_path = Path(root_path)
        
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the file."""
        try:
            stats = self.file_path.stat()
            return {
                'name': self.file_path.name,
                'path': str(self.file_path.relative_to(self.root_path)),
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'type': self.file_path.suffix.lstrip('.') or 'unknown'
            }
        except Exception as e:
            logger.error(f"Error getting file info for {self.file_path}: {str(e)}")
            return {
                'name': self.file_path.name,
                'path': str(self.file_path),
                'size': 0,
                'modified': 'unknown',
                'type': 'unknown'
            }
            
    def read_file(self) -> str:
        """Read the contents of the file."""
        try:
            return self.file_path.read_text()
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {str(e)}")
            return f"Error reading file: {str(e)}"

def render_file_viewer(config: Dict[str, Any], file_handler: FileHandler, crawler: RepositoryCrawler) -> Optional[str]:
    """Render the file viewer component."""
    try:
        # Get selected file from session state
        selected_file = st.session_state.get('selected_file')
        if not selected_file:
            return None
            
        # Create file viewer instance
        viewer = FileViewer(selected_file, config['path'])
        file_info = viewer.get_file_info()
        
        # Display file information
        st.subheader(f"File: {file_info['path']}")
        
        cols = st.columns(3)
        with cols[0]:
            st.metric("Size", f"{file_info['size']} bytes")
        with cols[1]:
            st.metric("Type", file_info['type'])
        with cols[2]:
            st.metric("Modified", file_info['modified'])
            
        # Display file contents
        st.code(viewer.read_file(), language=file_info['type'])
        
        return selected_file
        
    except Exception as e:
        logger.error(f"Error rendering file viewer: {str(e)}")
        st.error("Error viewing file. Please check the logs for details.")
        return None