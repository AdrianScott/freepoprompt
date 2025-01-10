# Repo_Crawler/frontend/components/file_tree.py

import streamlit as st
from pathlib import Path
import logging
from typing import Optional, Set, Dict, Any
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler

logger = logging.getLogger(__name__)

class FileTreeComponent:
    """Component for displaying and interacting with the file tree."""
    
    def __init__(self, file_tree: Dict[str, Any]):
        """Initialize the file tree component."""
        self.file_tree = file_tree
        self.expanded_nodes = set()  # Track expanded nodes
        
    def _render_node(self, node: Dict[str, Any], indent_level: int = 0) -> Optional[str]:
        """Render a single node in the file tree."""
        try:
            path = Path(node['path'])
            name = path.name or str(path)
            is_dir = node['type'] == 'directory'
            
            # Create unique key for this node
            node_key = f"{path}_{indent_level}"
            
            # Indent the node
            indent = "    " * indent_level
            
            # Create the display text
            if is_dir:
                icon = "📁" if node_key not in self.expanded_nodes else "📂"
            else:
                icon = "📄"
            display_text = f"{indent}{icon} {name}"
            
            # Create a clickable element
            if st.button(
                display_text,
                key=node_key,
                help=f"Click to {'expand/collapse' if is_dir else 'view'} {path}"
            ):
                if is_dir:
                    # Toggle directory expansion
                    if node_key in self.expanded_nodes:
                        self.expanded_nodes.remove(node_key)
                    else:
                        self.expanded_nodes.add(node_key)
                    return None
                else:
                    # Select file for viewing
                    return str(path)
            
            # If this is an expanded directory, render its children
            if is_dir and node_key in self.expanded_nodes:
                for child in node.get('children', []):
                    selected = self._render_node(child, indent_level + 1)
                    if selected:
                        return selected
            
            return None
            
        except Exception as e:
            logger.error(f"Error rendering node {node.get('path', 'unknown')}: {str(e)}")
            return None
            
    def render(self) -> Optional[str]:
        """Render the file tree component."""
        try:
            st.subheader("File Tree")
            
            # Add a search box
            search_term = st.text_input(
                "Search files",
                key="file_tree_search",
                help="Enter text to filter files and directories"
            ).lower()
            
            # Render the tree
            return self._render_node(self.file_tree)
            
        except Exception as e:
            logger.error(f"Error rendering file tree: {str(e)}")
            st.error("Error rendering file tree. Please check the logs for details.")
            return None

def _generate_tree_structure(root_path: Path, file_tree: Dict[str, Any], prefix: str = "") -> str:
    """Generate a tree-style ASCII representation of the project structure."""
    try:
        if not file_tree:
            return ""
            
        lines = []
        path = Path(file_tree['path'])
        name = path.name or str(path)
        
        # Add this node
        if prefix:  # Not root
            lines.append(f"{prefix}{'└── ' if prefix.endswith('    ') else '├── '}{name}")
        
        # Process children if this is a directory
        if file_tree['type'] == 'directory' and 'children' in file_tree:
            children = file_tree['children']
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                new_prefix = prefix + ('    ' if prefix.endswith('    ') or not prefix else '│   ')
                child_tree = _generate_tree_structure(root_path, child, new_prefix)
                if child_tree:
                    lines.append(child_tree)
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error generating tree structure: {str(e)}")
        return ""

def render_file_tree(config: Dict[str, Any], file_handler: FileHandler, crawler: RepositoryCrawler) -> Optional[str]:
    """Render the file tree component."""
    try:
        # Get the file tree from the crawler
        file_tree = crawler.get_file_tree()
        
        # Add Generate File Tree button
        if st.button("Generate File Tree", key="generate_file_tree"):
            # Generate ASCII tree structure
            tree_structure = _generate_tree_structure(Path(config.get('path', '')), file_tree)
            if tree_structure:
                st.code(tree_structure, language="")
        
        # Create and render the component
        component = FileTreeComponent(file_tree)
        return component.render()
    except Exception as e:
        logger.error(f"Error rendering file tree: {str(e)}")
        st.error("Error rendering file tree. Please check the logs for details.")
        return None
