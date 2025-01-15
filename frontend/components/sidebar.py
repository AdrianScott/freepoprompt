"""Sidebar component for the application."""

import streamlit as st
import yaml
import logging
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional
from backend.core.user_settings import (
    load_defaults,
    load_user_settings,
    save_user_settings,
    get_effective_settings,
    get_user_settings_path
)
from backend.core.models import IgnorePatterns

logger = logging.getLogger(__name__)

class SidebarComponent:
    """Sidebar component for managing application settings."""
    
    _instance = None
    _config_lock = Lock()
    _save_timer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SidebarComponent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            logger.info("Initializing SidebarComponent")
            self.initialize_state()
            self._initialized = True

    def initialize_state(self):
        """Initialize session state with defaults and user settings."""
        if 'needs_save' not in st.session_state:
            st.session_state.needs_save = False
        if 'last_config' not in st.session_state:
            st.session_state.last_config = None
            
        with self._config_lock:
            if 'defaults' not in st.session_state:
                st.session_state.defaults = load_defaults()
            if 'user_settings' not in st.session_state:
                st.session_state.user_settings = load_user_settings()
            if 'config' not in st.session_state:
                st.session_state.config = get_effective_settings()
                st.session_state.last_config = st.session_state.config.copy()

            # Initialize loaded_rules from saved_rules in config
            if 'loaded_rules' not in st.session_state:
                st.session_state.loaded_rules = st.session_state.config.get('saved_rules', {}).copy()

            # Initialize rule editing state
            if 'creating_new_rule' not in st.session_state:
                st.session_state.creating_new_rule = False
            if 'editing_rule' not in st.session_state:
                st.session_state.editing_rule = None
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

    def queue_save_config(self, config_data: Dict[str, Any]):
        """Queue config changes to be saved."""
        # Make a deep copy to ensure last_config comparison works
        st.session_state.config = config_data.copy()
        # Force save by clearing last_config
        st.session_state.last_config = None
        st.session_state.needs_save = True
        logger.info("Config save queued and forced by clearing last_config")

    def save_config_if_needed(self) -> bool:
        """Save config only if there are actual changes.
        
        Returns:
            bool: True if save was successful or not needed, False if save failed
        """
        logger.info("Checking if save needed...")
        if not st.session_state.needs_save:
            logger.info("No save needed (needs_save is False)")
            return True
            
        with self._config_lock:
            logger.info("Acquired config lock for saving")
            current_config = st.session_state.config
            last_config = st.session_state.last_config
            
            logger.info(f"Current config: {current_config}")
            logger.info(f"Last config: {last_config}")
            
            # Always save if last_config is None (forced save)
            if last_config is None or current_config != last_config:
                logger.info("Config has changed or force save requested...")
                # Only save differences from defaults
                defaults = st.session_state.defaults
                user_settings = {
                    k: v for k, v in current_config.items() 
                    if k not in defaults or v != defaults[k]
                }
                logger.info(f"Saving user settings: {user_settings}")
                save_success = save_user_settings(user_settings)
                if save_success:
                    logger.info("Config saved successfully")
                    st.session_state.user_settings = user_settings
                    st.session_state.last_config = current_config.copy()
                    st.session_state.needs_save = False
                    return True
                else:
                    logger.error("Failed to save config")
                    return False
            else:
                logger.info("Config unchanged, no save needed")
            
            return True

    def load_config_file(self, uploaded_file) -> bool:
        """Load configuration from uploaded file."""
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            config_data = yaml.safe_load(content)
            if isinstance(config_data, dict):
                self.queue_save_config(config_data)
                return True
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
        return False

    def clear_state(self):
        """Clear all sidebar-related state."""
        # Keep creating_new_rule state
        creating_new_rule = st.session_state.get('creating_new_rule', False)
        
        # Clear state
        st.session_state.loaded_rules = {}
        st.session_state.editing_rule = None
        st.session_state.new_rule_name = ""
        st.session_state.new_rule_content = ""
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
            
        # Restore creating_new_rule state
        st.session_state.creating_new_rule = creating_new_rule
        
        self.queue_save_config(st.session_state.defaults)

    def _add_rule(self, rule_name: str, rule_content: str) -> bool:
        """Add a new rule with proper error handling and state management.
        
        Args:
            rule_name: Name of the rule to add
            rule_content: Content of the rule
            
        Returns:
            bool: True if rule was added successfully
        """
        try:
            logger.info(f"[Add] Processing rule: {rule_name}")
            logger.info(f"[Add] Content length: {len(rule_content)} chars")
            
            # Initialize if needed
            if 'saved_rules' not in st.session_state.config:
                logger.info("[Add] Initializing saved_rules in config")
                st.session_state.config['saved_rules'] = {}
            if 'loaded_rules' not in st.session_state:
                logger.info("[Add] Initializing loaded_rules in session")
                st.session_state.loaded_rules = {}
            
            # Save rule
            logger.info(f"[Add] Saving rule to config and session...")
            st.session_state.config['saved_rules'][rule_name] = rule_content
            st.session_state.loaded_rules[rule_name] = rule_content
            
            # Force immediate save
            logger.info("[Add] Queueing config save...")
            self.queue_save_config(st.session_state.config)
            
            logger.info("[Add] Forcing immediate save...")
            save_success = self.save_config_if_needed()
            
            if save_success:
                logger.info("[Add] Save successful")
                st.success(f"Rule '{rule_name}' added successfully!")
            else:
                logger.error("[Add] Save failed")
                st.error("Failed to save rule to config file")
                return False
            
            logger.info(f"[Add] Final state - loaded_rules: {st.session_state.loaded_rules}")
            logger.info(f"[Add] Final state - config saved_rules: {st.session_state.config.get('saved_rules', {})}")
            
            return True
            
        except Exception as e:
            logger.error(f"[Add] Error adding rule: {str(e)}", exc_info=True)
            st.error(f"Error adding rule: {str(e)}")
            return False

    def _render_rules_tab(self):
        """Render the rules management tab."""
        logger.info("=== Starting _render_rules_tab ===")
        logger.info(f"Current loaded_rules: {st.session_state.loaded_rules}")
        logger.info(f"Current config saved_rules: {st.session_state.config.get('saved_rules', {})}")
        
        st.markdown("### Rules Management")
        
        # Debug info
        with st.expander("Debug Info"):
            st.write("Current Rules:", st.session_state.loaded_rules)
            st.write("Config Rules:", st.session_state.config.get('saved_rules', {}))
            st.write("Needs Save:", st.session_state.needs_save)
            st.write("Config Path:", get_user_settings_path())
        
        # Add rule section
        st.markdown("#### Add Rule")
        
        # File upload for rules
        uploaded_file = st.file_uploader(
            "Upload a rule file",
            type=['txt', 'md'],
            key="rule_uploader",
            help="Drag and drop or browse for a rule file"
        )
        
        if uploaded_file is not None:
            try:
                # Get the rule content
                rule_content = uploaded_file.getvalue().decode()
                rule_name = Path(uploaded_file.name).stem
                
                if self._add_rule(rule_name, rule_content):
                    # Clear the uploader state
                    st.session_state.rule_uploader = None
                    st.rerun()
                    
            except Exception as e:
                logger.error(f"[Upload] Error processing file: {str(e)}", exc_info=True)
                st.error(f"Error processing file: {str(e)}")

        # Manual rule creation
        create_new = st.button("Create New Rule", key="create_rule")
        if create_new:
            logger.info("[Create] Initializing new rule creation...")
            st.session_state.creating_new_rule = True
            st.rerun()

        # Rule creation form
        if st.session_state.get('creating_new_rule', False):
            logger.info("[Create] Rendering rule creation form")
            st.markdown("#### Create New Rule")
            with st.form(key="new_rule_form"):
                new_rule_name = st.text_input(
                    "Rule Name",
                    value="",
                    key="new_rule_name_input"
                )
                
                new_rule_content = st.text_area(
                    "Rule Content",
                    value="",
                    height=200,
                    key="new_rule_content_input",
                    help="Enter the content of your rule"
                )

                submit = st.form_submit_button("Save Rule")
                cancel = st.form_submit_button("Cancel")

                if submit and new_rule_name and new_rule_content:
                    if self._add_rule(new_rule_name, new_rule_content):
                        # Clear form state
                        st.session_state.creating_new_rule = False
                        st.rerun()
                
                elif cancel:
                    logger.info("[Create] Canceling rule creation")
                    st.session_state.creating_new_rule = False
                    st.rerun()

        # Show existing rules
        st.markdown("#### Existing Rules")
        if not st.session_state.loaded_rules:
            st.info("No rules added yet")
        else:
            for rule_name, rule_content in st.session_state.loaded_rules.items():
                with st.expander(rule_name):
                    st.code(rule_content)
                    if st.button("Delete", key=f"delete_{rule_name}"):
                        try:
                            logger.info(f"[Delete] Deleting rule: {rule_name}")
                            
                            # Remove from session
                            logger.info("[Delete] Removing from loaded_rules")
                            del st.session_state.loaded_rules[rule_name]
                            
                            # Remove from config
                            if rule_name in st.session_state.config.get('saved_rules', {}):
                                logger.info("[Delete] Removing from config saved_rules")
                                del st.session_state.config['saved_rules'][rule_name]
                                
                                # Force immediate save
                                logger.info("[Delete] Queueing config save...")
                                self.queue_save_config(st.session_state.config)
                                
                                logger.info("[Delete] Forcing immediate save...")
                                save_success = self.save_config_if_needed()
                                
                                if save_success:
                                    logger.info("[Delete] Save successful")
                                    st.success(f"Rule '{rule_name}' deleted successfully!")
                                else:
                                    logger.error("[Delete] Save failed")
                                    st.error("Failed to save config after deleting rule")
                            
                            logger.info(f"[Delete] Final state - loaded_rules: {st.session_state.loaded_rules}")
                            logger.info(f"[Delete] Final state - config saved_rules: {st.session_state.config.get('saved_rules', {})}")
                            
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"[Delete] Error deleting rule: {str(e)}", exc_info=True)
                            st.error(f"Error deleting rule: {str(e)}")
        
        logger.info("=== Finished _render_rules_tab ===")

    def _render_files_tab(self):
        """Render the files management tab."""
        st.markdown("### Files Settings")

        # Default ignore patterns
        default_ignore = IgnorePatterns()

        # Ignored directories
        st.markdown("#### Ignored Directories")
        ignored_dirs = st.session_state.config.get('ignore_patterns', {}).get('directories', default_ignore.directories)
        ignored_dirs_str = '\n'.join(ignored_dirs)
        new_ignored_dirs = st.text_area(
            "One directory pattern per line",
            value=ignored_dirs_str,
            height=150,
            help="Directory patterns to ignore (e.g., node_modules, .git). Leave empty to use defaults."
        )
        if new_ignored_dirs != ignored_dirs_str:
            new_dirs = [d.strip() for d in new_ignored_dirs.split('\n') if d.strip()]
            if not new_dirs:  # If empty, use defaults
                new_dirs = default_ignore.directories
            if 'ignore_patterns' not in st.session_state.config:
                st.session_state.config['ignore_patterns'] = {'directories': [], 'files': []}
            st.session_state.config['ignore_patterns']['directories'] = new_dirs
            self.queue_save_config(st.session_state.config)

        # Ignored files
        st.markdown("#### Ignored Files")
        ignored_files = st.session_state.config.get('ignore_patterns', {}).get('files', default_ignore.files)
        ignored_files_str = '\n'.join(ignored_files)
        new_ignored_files = st.text_area(
            "One file pattern per line",
            value=ignored_files_str,
            height=150,
            help="File patterns to ignore (e.g., *.pyc, *.log). Leave empty to use defaults."
        )
        if new_ignored_files != ignored_files_str:
            new_files = [f.strip() for f in new_ignored_files.split('\n') if f.strip()]
            if not new_files:  # If empty, use defaults
                new_files = default_ignore.files
            if 'ignore_patterns' not in st.session_state.config:
                st.session_state.config['ignore_patterns'] = {'directories': [], 'files': []}
            st.session_state.config['ignore_patterns']['files'] = new_files
            self.queue_save_config(st.session_state.config)

    def render(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("Settings")
            
            # Create tabs
            settings_tab, rules_tab, files_tab = st.tabs(["Settings", "Rules", "Files"])
            
            # Settings tab - contains all configuration
            with settings_tab:
                # Model selection
                st.markdown("### Model Settings")
                model = st.selectbox(
                    "Token Analysis Model",
                    options=["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                    index=["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"].index(
                        st.session_state.config.get('model', 'gpt-4')
                    ),
                    help="Select the model to use for token analysis"
                )
                if model != st.session_state.config.get('model', 'gpt-4'):
                    st.session_state.config['model'] = model
                    self.queue_save_config(st.session_state.config)

                # Path style selection
                st.markdown("### Path Settings")
                use_relative = st.toggle(
                    "Use Relative Paths",
                    value=st.session_state.config.get('use_relative_paths', True),
                    help="If enabled, file paths will be relative to the repository root"
                )
                if use_relative != st.session_state.config.get('use_relative_paths', True):
                    st.session_state.config['use_relative_paths'] = use_relative
                    self.queue_save_config(st.session_state.config)

                # Repository path
                st.markdown("### Repository")
                repo_path = st.text_input(
                    "Path",
                    value=st.session_state.config.get('path', ''),
                    help="Enter the full path to your local repository",
                    placeholder="/path/to/repository"
                )

                if st.button("Browse for Repository", help="Browse for repository directory", use_container_width=True):
                    # Use system file dialog
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    root.attributes('-topmost', True)  # Bring dialog to front
                    selected_path = filedialog.askdirectory()
                    root.destroy()

                    if selected_path:
                        repo_path = str(Path(selected_path))
                        st.session_state.config['path'] = repo_path
                        self.queue_save_config(st.session_state.config)
                        st.rerun()

                if repo_path != st.session_state.config.get('path', ''):
                    st.session_state.config['path'] = repo_path
                    self.queue_save_config(st.session_state.config)

            # Rules tab
            with rules_tab:
                self._render_rules_tab()
            
            # Files tab
            with files_tab:
                self._render_files_tab()
                
            # Save any pending changes at the end of rendering
            self.save_config_if_needed()