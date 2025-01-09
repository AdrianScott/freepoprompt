"""Main entry point for the application."""

import streamlit as st
import logging
from pathlib import Path
from backend.core.config import load_config
from frontend.dashboard import render_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    try:
        # Set page config
        st.set_page_config(
            page_title="Repository Analyzer",
            page_icon="",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if 'config' not in st.session_state:
            st.session_state.config = load_config()
            logger.info("Configuration and session state reset to default values (excluding loaded_rules)")
            
        # Render dashboard
        render_dashboard()
        
    except Exception as e:
        logger.error("Unhandled exception in main", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        
if __name__ == "__main__":
    main()
