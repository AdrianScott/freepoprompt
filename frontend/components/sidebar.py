"""Sidebar component for the application."""

import streamlit as st
import yaml
from pathlib import Path
import logging
from threading import Lock
from typing import Dict, Any, Optional
from backend.core.user_settings import (
    load_defaults,
    load_user_settings,
    save_user_settings,
    get_effective_settings
)

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
            
            # Rules-related state
            if 'loaded_rules' not in st.session_state:
                st.session_state.loaded_rules = st.session_state.config.get('saved_rules', {})
            if 'editing_rule' not in st.session_state:
                st.session_state.editing_rule = None
            if 'creating_new_rule' not in st.session_state:
                st.session_state.creating_new_rule = False
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
        st.session_state.config = config_data
        st.session_state.needs_save = True

    def save_config_if_needed(self):
        """Save config only if there are actual changes."""
        if not st.session_state.needs_save:
            return
            
        with self._config_lock:
            current_config = st.session_state.config
            last_config = st.session_state.last_config
            
            if current_config != last_config:
                # Only save differences from defaults
                defaults = st.session_state.defaults
                user_settings = {
                    k: v for k, v in current_config.items() 
                    if k not in defaults or v != defaults[k]
                }
                if save_user_settings(user_settings):
                    st.session_state.user_settings = user_settings
                    st.session_state.last_config = current_config.copy()
                    
            st.session_state.needs_save = False

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
        st.session_state.user_settings = {}
        st.session_state.config = st.session_state.defaults.copy()
        st.session_state.loaded_config = None
        st.session_state.loaded_rules = {}
        st.session_state.creating_new_rule = False
        st.session_state.editing_rule = None
        st.session_state.new_rule_name = ""
        st.session_state.new_rule_content = ""
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
        self.queue_save_config(st.session_state.defaults)

    def _render_rules_tab(self):
        """Render the rules management tab."""
        st.markdown("### Rules Management")

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
                # Use filename without extension as rule name
                rule_name = Path(uploaded_file.name).stem
                
                # Save rule
                st.session_state.config.setdefault('saved_rules', {})
                st.session_state.config['saved_rules'][rule_name] = rule_content
                st.session_state.loaded_rules[rule_name] = rule_content
                self.queue_save_config(st.session_state.config)
                
                # Set this rule for editing
                st.session_state.editing_rule = rule_name
                st.rerun()
            except Exception as e:
                st.error(f"Error adding rule: {str(e)}")

        # Manual rule creation
        if st.button("Create New Rule", key="create_rule"):
            st.session_state.creating_new_rule = True
            st.session_state.editing_rule = None

        # Rule creation/editing form
        if st.session_state.get('creating_new_rule', False) or st.session_state.get('editing_rule'):
            editing = st.session_state.get('editing_rule')
            form_key = "edit_rule" if editing else "new_rule"
            
            with st.form(key=form_key):
                # If editing, pre-fill the fields
                default_name = editing if editing else st.session_state.get('new_rule_name', '')
                default_content = (st.session_state.loaded_rules.get(editing, '') 
                                if editing else st.session_state.get('new_rule_content', ''))
                
                new_rule_name = st.text_input("Rule Name", 
                                            value=default_name,
                                            disabled=editing is not None,
                                            key=f"{form_key}_name")
                
                new_rule_content = st.text_area("Rule Content",
                                              value=default_content,
                                              height=200,
                                              key=f"{form_key}_content",
                                              help="Enter the content of your rule")

                col1, col2 = st.columns([1, 1])
                with col1:
                    submit = st.form_submit_button("Save Rule")
                with col2:
                    cancel = st.form_submit_button("Cancel")

                if submit and new_rule_name and new_rule_content:
                    # Save rule to config
                    st.session_state.config.setdefault('saved_rules', {})
                    st.session_state.config['saved_rules'][new_rule_name] = new_rule_content
                    st.session_state.loaded_rules[new_rule_name] = new_rule_content
                    self.queue_save_config(st.session_state.config)
                    
                    # Clear form state
                    st.session_state.creating_new_rule = False
                    st.session_state.editing_rule = None
                    st.session_state.new_rule_name = ""
                    st.session_state.new_rule_content = ""
                    st.rerun()
                
                elif cancel:
                    st.session_state.creating_new_rule = False
                    st.session_state.editing_rule = None
                    st.session_state.new_rule_name = ""
                    st.session_state.new_rule_content = ""
                    st.rerun()

        # Show existing rules
        st.markdown("#### Existing Rules")
        if not st.session_state.loaded_rules:
            st.info("No rules added yet")
        else:
            for rule_name, rule_content in st.session_state.loaded_rules.items():
                with st.expander(rule_name):
                    if st.session_state.get('editing_rule') == rule_name:
                        # Edit mode - show text area with save button
                        edited_content = st.text_area(
                            "Rule Content",
                            value=rule_content,
                            height=200,
                            key=f"edit_{rule_name}_content"
                        )
                        if st.button("Save", key=f"save_{rule_name}"):
                            # Save edited content
                            st.session_state.config['saved_rules'][rule_name] = edited_content
                            st.session_state.loaded_rules[rule_name] = edited_content
                            self.queue_save_config(st.session_state.config)
                            st.session_state.editing_rule = None
                            st.rerun()
                    else:
                        # View mode - show content and edit/delete buttons
                        st.code(rule_content)
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Update", key=f"edit_{rule_name}"):
                                st.session_state.editing_rule = rule_name
                                st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_{rule_name}"):
                                del st.session_state.loaded_rules[rule_name]
                                if rule_name in st.session_state.config.get('saved_rules', {}):
                                    del st.session_state.config['saved_rules'][rule_name]
                                    self.queue_save_config(st.session_state.config)
                                st.rerun()

    def _render_files_tab(self):
        """Render the files management tab."""
        st.markdown("### File Filtering")
        
        # Create subtabs for patterns and preview
        patterns_tab, preview_tab = st.tabs(["Patterns", "Preview"])
        
        with patterns_tab:
            # Directory patterns
            st.write("Directory Patterns")
            dir_patterns = st.text_area(
                "Enter directory patterns to ignore (one per line)",
                value="\n".join(st.session_state.config.get('ignore_patterns', {}).get('directories', [])),
                help="Example: node_modules, .git, __pycache__",
                key="sidebar_dir_patterns"
            )
            
            # File patterns
            st.write("File Patterns")
            file_patterns = st.text_area(
                "Enter file patterns to ignore (one per line)",
                value="\n".join(st.session_state.config.get('ignore_patterns', {}).get('files', [])),
                help="Example: *.pyc, *.log, .env",
                key="sidebar_file_patterns"
            )
            
            # Update button
            if st.button("Update Ignore Patterns", key="sidebar_update_patterns"):
                # Parse patterns
                dir_list = [p.strip() for p in dir_patterns.split('\n') if p.strip()]
                file_list = [p.strip() for p in file_patterns.split('\n') if p.strip()]
                
                # Update config
                st.session_state.config['ignore_patterns'] = {
                    'directories': dir_list,
                    'files': file_list
                }
                self.queue_save_config(st.session_state.config)
                st.success("Ignore patterns updated!")
        
        with preview_tab:
            st.write("Ignored Patterns Preview")
            patterns = st.session_state.config.get('ignore_patterns', {})
            
            if patterns.get('directories'):
                st.write("Directories:")
                for pattern in patterns['directories']:
                    st.code(pattern)
            
            if patterns.get('files'):
                st.write("Files:")
                for pattern in patterns['files']:
                    st.code(pattern)

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