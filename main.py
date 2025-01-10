"""Main entry point for the application."""

import streamlit as st
import logging
from pathlib import Path
from backend.core.user_settings import get_effective_settings
from frontend.dashboard import render_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

        # Load and apply configuration
        config = get_effective_settings()
        
        # Render dashboard
        render_dashboard()

    except Exception as e:
        logger.exception("Error in main")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
