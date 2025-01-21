"""Main entry point for the application."""

import streamlit as st
import logging
import os
from pathlib import Path
from backend.core.user_settings import get_effective_settings, load_defaults, load_user_settings
from frontend.dashboard import render_dashboard

# Ensure logs directory exists
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize all session state variables."""
    # Basic config state
    if 'needs_save' not in st.session_state:
        st.session_state.needs_save = False
    if 'last_config' not in st.session_state:
        st.session_state.last_config = None
    if 'defaults' not in st.session_state:
        st.session_state.defaults = load_defaults()
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = load_user_settings()
    if 'config' not in st.session_state:
        st.session_state.config = get_effective_settings()
        st.session_state.last_config = st.session_state.config.copy()

    # Rules state
    if 'loaded_rules' not in st.session_state:
        st.session_state.loaded_rules = st.session_state.config.get('saved_rules', {}).copy()
    if 'creating_new_rule' not in st.session_state:
        st.session_state.creating_new_rule = False
    if 'editing_rule' not in st.session_state:
        st.session_state.editing_rule = None
    if 'editing_rule_content' not in st.session_state:
        st.session_state.editing_rule_content = ""
    if 'new_rule_name' not in st.session_state:
        st.session_state.new_rule_name = ""
    if 'new_rule_content' not in st.session_state:
        st.session_state.new_rule_content = ""

    # Other state
    if 'loaded_config' not in st.session_state:
        st.session_state.loaded_config = None
    if 'current_tree' not in st.session_state:
        st.session_state.current_tree = None
    if 'crawler' not in st.session_state:
        st.session_state.crawler = None
    if 'config_hash' not in st.session_state:
        st.session_state.config_hash = None

def main():
    """Main entry point."""
    try:
        # Set page config
        st.set_page_config(
            page_title="Prompt Prep",
            page_icon="📝",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize all session state
        initialize_session_state()
        
        # Render dashboard
        render_dashboard()

    except Exception as e:
        logger.exception("Error in main")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
