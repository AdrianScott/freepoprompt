"""Main dashboard component."""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Any
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler
from backend.core.config import load_config, save_config
from frontend.components.file_tree import render_file_tree
from frontend.components.file_viewer import render_file_viewer
from frontend.codebase_view import render_codebase_view
from frontend.components.sidebar import SidebarComponent

def render_dashboard():
    """Render the main dashboard."""
    # Render sidebar first
    sidebar = SidebarComponent()
    sidebar.render()

    st.title("Prompt Prep")

    try:
        # Load configuration
        config = load_config()

        # Show repository info
        repo_path = config.get('path', '')
        if repo_path:
            st.markdown(f"**Selected Repository:** `{repo_path}`")
            if not os.path.exists(repo_path):
                st.warning(f"Repository path does not exist: {repo_path}")
        else:
            st.warning("No repository selected")

        # Initialize file handler and crawler
        file_handler = FileHandler(config['path'])
        crawler = RepositoryCrawler(config['path'], config)

        # Create columns for layout
        file_explorer, code_viewer = st.columns([1, 2])  # Renamed columns for clarity

        with file_explorer:  # Left column for file tree
            # Render file tree
            render_file_tree(config, file_handler, crawler)

        with code_viewer:  # Right column for viewing and analyzing code
            # Render file viewer
            render_file_viewer(config, file_handler, crawler)

            # Render codebase view
            render_codebase_view(file_handler, crawler)

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.stop()