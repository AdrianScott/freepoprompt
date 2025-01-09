"""Component for displaying and managing ignore patterns."""

import streamlit as st
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler

logger = logging.getLogger(__name__)

class IgnoreTreeComponent:
    """Component for displaying and managing ignore patterns."""
    
    def __init__(self, file_tree: Dict[str, Any]):
        """Initialize the ignore tree component."""
        self.file_tree = file_tree
        
    def _render_ignore_patterns(self) -> None:
        """Render the ignore patterns section."""
        try:
            st.subheader("Ignore Patterns")
            
            # Directory patterns
            st.write("Directory Patterns")
            dir_patterns = st.text_area(
                "Enter directory patterns to ignore (one per line)",
                value="\n".join(self.file_tree.get('ignore_patterns', {}).get('directories', [])),
                key=f"dir_patterns_{id(self)}",
                help="Example: node_modules, .git, __pycache__"
            )
            
            # File patterns
            st.write("File Patterns")
            file_patterns = st.text_area(
                "Enter file patterns to ignore (one per line)",
                value="\n".join(self.file_tree.get('ignore_patterns', {}).get('files', [])),
                key=f"file_patterns_{id(self)}",
                help="Example: *.pyc, *.log, .env"
            )
            
            # Update button
            if st.button("Update Ignore Patterns", key=f"update_patterns_{id(self)}"):
                # Parse patterns
                dir_list: List[str] = [p.strip() for p in dir_patterns.split('\n') if p.strip()]
                file_list: List[str] = [p.strip() for p in file_patterns.split('\n') if p.strip()]
                
                # Update config
                self.file_tree['ignore_patterns'] = {
                    'directories': dir_list,
                    'files': file_list
                }
                
                st.success("Ignore patterns updated!")
                
        except Exception as e:
            logger.error(f"Error rendering ignore patterns: {str(e)}")
            st.error("Error updating ignore patterns")
            
    def _render_preview(self) -> None:
        """Render a preview of what will be ignored."""
        try:
            st.subheader("Preview")
            
            # Get current patterns
            patterns: Optional[Dict[str, Any]] = self.file_tree.get('ignore_patterns')
            dir_patterns: List[str] = patterns.get('directories', []) if patterns else []
            file_patterns: List[str] = patterns.get('files', []) if patterns else []
            
            # Display current patterns
            if dir_patterns:
                st.write("Ignored Directories:")
                for i, pattern in enumerate(dir_patterns):
                    st.code(pattern, key=f"dir_preview_{id(self)}_{i}")
                    
            if file_patterns:
                st.write("Ignored Files:")
                for i, pattern in enumerate(file_patterns):
                    st.code(pattern, key=f"file_preview_{id(self)}_{i}")
                    
            # TODO: Add preview of which files would be ignored
            
        except Exception as e:
            logger.error(f"Error rendering preview: {str(e)}")
            st.error("Error rendering preview")
            
    def render(self) -> None:
        """Render the ignore tree component."""
        try:
            # Create tabs for different sections
            tab1, tab2 = st.tabs(["Patterns", "Preview"])
            
            with tab1:
                self._render_ignore_patterns()
                
            with tab2:
                self._render_preview()
                
        except Exception as e:
            logger.error(f"Error rendering ignore tree: {str(e)}")
            st.error("Error rendering ignore patterns")

def render_ignore_tree(config: Dict[str, Any], file_handler: FileHandler, crawler: RepositoryCrawler) -> None:
    """Render the ignore tree component."""
    component = IgnoreTreeComponent(config)
    component.render()
