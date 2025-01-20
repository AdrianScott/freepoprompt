"""Main dashboard component."""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Any
from urllib.parse import quote
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler
from backend.core.user_settings import get_effective_settings, save_user_settings
from frontend.components.file_tree import render_file_tree
from frontend.components.file_viewer import render_file_viewer
from frontend.codebase_view import render_codebase_view
from frontend.components.sidebar import SidebarComponent
import logging
logger = logging.getLogger(__name__)

def render_social_links():
    """Render social media links with button-like appearance."""
    # Add Font Awesome
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)
    
    tweet_text = quote("I'm using FreepoPrompt from @AdrianDoesAI for my A.I. coding")
    
    st.markdown(f"""
<style>
.social-links {{ 
    display: flex; 
    flex-direction: column; 
    gap: 6px; 
    margin: 12px 0;
    opacity: 0.95;
}}
.social-button {{ 
    display: flex; 
    align-items: center; 
    padding: 8px 12px; 
    background-color: #f0f0f0; 
    color: #333333 !important; 
    text-decoration: none; 
    border-radius: 3px; 
    transition: all 0.15s ease; 
    border: 1px solid #d8d8d8; 
    font-size: 13.5px; 
    font-weight: 400;
    letter-spacing: 0.2px;
}}
.social-button:hover {{ 
    background-color: #e8e8e8; 
    color: #222222 !important;
    border-color: #cccccc; 
}}
.social-button i {{ 
    margin-right: 8px; 
    font-size: 14px;
    opacity: 0.9;
}}
</style>
<div class="social-links">
    <a href="https://x.com/intent/tweet?text={tweet_text}" class="social-button" target="_blank">
        <i class="fa-solid fa-share"></i>Share on X
    </a>
    <a href="https://x.com/intent/follow?screen_name=AdrianDoesAI" class="social-button" target="_blank">
        <i class="fa-solid fa-user-plus"></i>Follow @AdrianDoesAI
    </a>
    <a href="https://discord.gg/uQjNv9pWFm" class="social-button" target="_blank">
        <i class="fab fa-discord"></i>Join Discord
    </a>
    <a href="https://www.github.com/AdrianScott/freepoprompt" class="social-button" target="_blank">
        <i class="fab fa-github"></i>Check the GitHub
    </a>
</div>
""", unsafe_allow_html=True)

def render_instructions():
    """Render usage instructions."""
    st.markdown("### Instructions")
    st.markdown("""
    1. Select your code repository's directory in the **Settings** tab at left
    2. Add any rules files (e.g. `o1-format.txt` and `instructions.txt`) with what you want changed in the **Rules** tab section at left
    3. You can exclude file directories or extensions through the **Files** tab
    4. Click **Generate File Tree** to review the file tree
    5. Click **Generate Prompt** to generate the prompt for the repo, then hit the **Copy** button in the top right of the code
    6. Paste it into your LLM's chat window
    7. Paste the LLM's response into [o1-xml-parser](https://www.github.com/AdrianScott/o1-xml-parser) and local files will be updated with the changes
    """)

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
                return
            logger.info(f"Repository path exists: {repo_path}")
        else:
            logger.warning("No repository path selected")
            st.info("No repository selected. Please select a repository path in the sidebar.")
            return

        # Initialize file handler and crawler
        logger.info(f"Initializing handlers with path: {repo_path}")
        file_handler = FileHandler(repo_path)
        crawler = RepositoryCrawler(repo_path, config)

        # Create columns for layout
        file_explorer, code_viewer = st.columns([1, 2])

        with file_explorer:  # Left column for file tree
            # Render file tree
            render_file_tree(config, file_handler, crawler)
            # Add social links and instructions after file tree
            st.markdown("---")  # Add a separator
            render_social_links()
            st.markdown("---")  # Add a separator
            render_instructions()

        with code_viewer:  # Right column for viewing and analyzing code
            # Render file viewer
            render_file_viewer(config, file_handler, crawler)
            # Render codebase view
            render_codebase_view(file_handler, crawler)

    except Exception as e:
        logger.exception("Error in dashboard")
        st.error(f"Error loading dashboard: {str(e)}")
        st.stop()