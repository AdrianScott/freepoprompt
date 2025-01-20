"""Main dashboard component."""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Any
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler
from backend.core.user_settings import get_effective_settings, save_user_settings
from frontend.components.file_tree import render_file_tree
from frontend.components.file_viewer import render_file_viewer
from frontend.codebase_view import render_codebase_view
from frontend.components.sidebar import SidebarComponent
import logging
logger = logging.getLogger(__name__)

def render_dashboard():
    """Render the main dashboard."""
    # Render sidebar first
    sidebar = SidebarComponent()
    sidebar.render()

    st.title("Freepo Prompt")

    try:
        # Load configuration
        config = get_effective_settings()
        logger.info(f"Dashboard loaded config: {config}")

        # Show repository info
        repo_path = config.get('path', '')
        logger.info(f"Using repository path: {repo_path}")

        if repo_path:
            st.markdown(f"**Selected Repository:** `{repo_path}`")
            if not os.path.exists(repo_path):
                logger.error(f"Repository path does not exist: {repo_path}")
                st.warning(f"Repository path does not exist: {repo_path}")
                return  # Don't try to initialize handlers with invalid path
            logger.info(f"Repository path exists: {repo_path}")
        else:
            logger.warning("No repository path selected")
            st.info("No repository selected. Please select a repository path in the sidebar.")
            return  # Don't try to initialize handlers without a path

        # Initialize file handler and crawler
        logger.info(f"Initializing handlers with path: {repo_path}")
        file_handler = FileHandler(repo_path)
        crawler = RepositoryCrawler(repo_path, config)

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
        logger.exception("Error in dashboard")
        st.error(f"Error loading dashboard: {str(e)}")
        st.stop()