import streamlit as st
import yaml
from pathlib import Path
import logging
from typing import Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)

class SidebarComponent:
    _instance = None
    _config_lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SidebarComponent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            logger.info("Initializing SidebarComponent")
            # Default config includes a dictionary for storing system files/rules
            self.default_config = {
                'path': '',
                'ignore_patterns': {
                    'directories': [
                        '.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.env',
                        'build', 'dist', '.idea', '.vscode', '.vs', 'bin', 'obj', 'out', 'target',
                        'coverage', '.coverage', '.pytest_cache', '.mypy_cache', '.tox', '.eggs',
                        '.sass-cache', 'bower_components', 'jspm_packages', '.next', '.nuxt',
                        '.serverless', '.terraform', 'vendor'
                    ],
                    'files': [
                        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib', '*.egg',
                        '*.egg-info', '*.whl', '.DS_Store', '.env', '*.log', '*.swp', '*.swo',
                        '*.class', '*.jar', '*.war', '*.nar', '*.ear', '*.zip', '*.tar.gz',
                        '*.rar', '*.min.js', '*.min.css', '*.map', '.env.local',
                        '.env.development.local', '.env.test.local', '.env.production.local',
                        '.env.*', '*.sqlite', '*.db', '*.db-shm', '*.db-wal', '*.suo',
                        '*.user', '*.userosscache', '*.sln.docstates', 'thumbs.db', '*.cache',
                        '*.bak', '*.tmp', '*.temp', '*.pid', '*.seed', '*.pid.lock',
                        '*.tsbuildinfo', '.eslintcache', '.node_repl_history', '.yarn-integrity',
                        '.grunt', '.lock-wscript'
                    ]
                },
                'model': 'gpt-4',
                'use_relative_paths': True,
                # This dictionary will store the uploaded system files (like rules, instructions),
                # so we don't have to re-add them every time the app restarts
                'saved_rules': {}
            }
            self.initialize_state()
            self._initialized = True

    def initialize_state(self):
        """
        Initialize session state for sidebar with proper locking.
        This includes loading saved config data (including saved_rules),
        which ensures that system files are automatically restored on restart.
        """
        try:
            with self._config_lock:
                # If we haven't tracked loaded rules yet, initialize an empty dict
                if 'loaded_rules' not in st.session_state:
                    st.session_state.loaded_rules = {}

                # Load config into session state if needed
                if 'config' not in st.session_state:
                    st.session_state.config = self.load_config() or self.default_config.copy()

                # Ensure 'saved_rules' exists in the config
                if 'saved_rules' not in st.session_state.config:
                    st.session_state.config['saved_rules'] = {}

                # Merge any previously stored system files/rules into the current session
                st.session_state.loaded_rules.update(st.session_state.config.get('saved_rules', {}))

                if 'loaded_config' not in st.session_state:
                    st.session_state.loaded_config = None
                if 'current_tree' not in st.session_state:
                    st.session_state.current_tree = None
                if 'crawler' not in st.session_state:
                    st.session_state.crawler = None
                if 'config_hash' not in st.session_state:
                    st.session_state.config_hash = None
        except Exception as e:
            logger.error(f"Error initializing state: {str(e)}")
            raise

    def load_config(self):
        """Load configuration from config.yaml."""
        config_path = Path('config/config.yaml')
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config and isinstance(loaded_config, dict):
                        # Ensure all required fields exist
                        if 'path' not in loaded_config:
                            loaded_config['path'] = self.default_config['path']
                        if 'model' not in loaded_config:
                            loaded_config['model'] = self.default_config['model']
                        if 'use_relative_paths' not in loaded_config:
                            loaded_config['use_relative_paths'] = self.default_config['use_relative_paths']
                        if 'saved_rules' not in loaded_config:
                            loaded_config['saved_rules'] = {}

                        # Ensure ignore patterns structure
                        if 'ignore_patterns' not in loaded_config:
                            loaded_config['ignore_patterns'] = self.default_config['ignore_patterns'].copy()
                        else:
                            if 'directories' not in loaded_config['ignore_patterns']:
                                loaded_config['ignore_patterns']['directories'] = []
                            if 'files' not in loaded_config['ignore_patterns']:
                                loaded_config['ignore_patterns']['files'] = []

                        return loaded_config
                    else:
                        logger.warning("Invalid config file format")
            except Exception as e:
                logger.exception("Error loading config")
        return None

    def save_config(self, config_data: Dict[str, Any]):
        """
        Save configuration to config.yaml with proper locking.
        This includes saving any updated 'saved_rules' so that the system files
        are preserved between restarts.
        """
        try:
            with self._config_lock:
                logger.info(f"Saving config: {config_data}")
                config_path = Path('config/config.yaml')
                config_path.parent.mkdir(parents=True, exist_ok=True)

                # Write to temporary file first
                temp_path = config_path.with_suffix('.yaml.tmp')
                with open(temp_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

                # Atomic rename
                temp_path.replace(config_path)

                # Update session state within the lock
                st.session_state.config = config_data.copy()

                # Update config hash to trigger proper updates
                st.session_state.config_hash = str(hash(str(config_data)))

                return True
        except Exception as e:
            logger.exception("Error saving configuration")
            st.error(f"Failed to save configuration: {str(e)}")
            return False

    def load_config_file(self, uploaded_file) -> bool:
        """
        Load configuration from an uploaded YAML file.
        If it's valid, we replace the current config with it.
        """
        try:
            # Read and parse YAML content
            content = uploaded_file.getvalue().decode()
            config_data = yaml.safe_load(content)

            # Validate config structure
            required_keys = {'path', 'ignore_patterns', 'model'}
            if not all(key in config_data for key in required_keys):
                st.error("Invalid configuration file format")
                return False

            # Save the configuration, which will merge with defaults
            return self.save_config(config_data)

        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error(f"Error loading configuration: {str(e)}")
            return False

    def clear_state(self):
        """
        Clear all sidebar-related state, resetting to default config.
        This also clears all stored system files from both session state and config.
        """
        st.session_state.config = self.default_config.copy()
        st.session_state.loaded_config = None
        st.session_state.loaded_rules = {}
        if 'current_tree' in st.session_state:
            del st.session_state.current_tree
        if 'crawler' in st.session_state:
            del st.session_state.crawler
        if 'config_hash' in st.session_state:
            del st.session_state.config_hash
        self.save_config(self.default_config)

    def render(self):
        """Render the sidebar."""
        with st.sidebar:
            st.title("Repository Crawler ")

            # Create tabs for different settings
            settings_tab, files_tab = st.tabs(["Settings", "Files"])

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
                    self.save_config(st.session_state.config)

                # Path style selection
                st.markdown("### Path Settings")
                use_relative = st.toggle(
                    "Use Relative Paths",
                    value=st.session_state.config.get('use_relative_paths', True),
                    help="If enabled, file paths will be relative to the repository root"
                )
                if use_relative != st.session_state.config.get('use_relative_paths', True):
                    st.session_state.config['use_relative_paths'] = use_relative
                    self.save_config(st.session_state.config)

                # Repository path
                st.markdown("### Repository")
                repo_path = st.text_input(
                    "Path",
                    value=st.session_state.config.get('path', ''),
                    help="Enter the full path to your local repository",
                    placeholder="C:/path/to/repository"
                )

                if st.button(" Browse for Repository", help="Browse for repository directory", use_container_width=True):
                    # Use system file dialog
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    root.attributes('-topmost', True)  # Bring dialog to front
                    selected_path = filedialog.askdirectory()
                    root.destroy()

                    if selected_path:
                        # Convert to Windows path format
                        repo_path = str(Path(selected_path))
                        st.session_state.config['path'] = repo_path
                        self.save_config(st.session_state.config)
                        st.rerun()

                if repo_path != st.session_state.config.get('path', ''):
                    st.session_state.config['path'] = repo_path
                    self.save_config(st.session_state.config)

                # Configuration file management
                st.markdown("### Configuration")

                # Show which rule files have been loaded
                if st.session_state.loaded_rules:
                    st.write("Loaded rules found:", list(st.session_state.loaded_rules.keys()))
                    # Provide a remove button for each loaded file
                    for filename in list(st.session_state.loaded_rules.keys()):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"- {filename}")
                        with col2:
                            if st.button(" ", key=f"remove_rule_{filename}", help=f"Remove {filename}"):
                                # Remove from session state
                                del st.session_state.loaded_rules[filename]
                                # Also remove from the config
                                if filename in st.session_state.config['saved_rules']:
                                    del st.session_state.config['saved_rules'][filename]
                                self.save_config(st.session_state.config)
                                st.rerun()

                # Show config status and clear button
                if st.session_state.loaded_config:
                    st.success(f"Using config: {st.session_state.loaded_config}")
                    if st.button(" Clear All", key="clear_all_config"):
                        self.clear_state()
                        st.rerun()

                # File uploader for system files or config
                uploaded_files = st.file_uploader(
                    "Upload system files",
                    type=['yaml', 'yml', 'md', 'txt', 'cursorrules'],
                    help="Upload config.yaml, system instructions, prompt, or rule files",
                    accept_multiple_files=True,
                    key=f"config_uploader_{len(st.session_state.loaded_rules)}"
                )

                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        logger.info(f"Processing uploaded system file: {uploaded_file.name} ({uploaded_file.size} bytes)")
                        try:
                            # If it's a YAML config file, load it as a new config
                            if uploaded_file.name.endswith(('.yaml', '.yml')):
                                if self.load_config_file(uploaded_file):
                                    st.session_state.loaded_config = uploaded_file.name
                                    logger.info(f"Successfully loaded config file: {uploaded_file.name}")
                                    st.success("Configuration loaded successfully!")
                                else:
                                    logger.error(f"Failed to load config file: {uploaded_file.name}")
                                    st.error(f"Failed to load config from {uploaded_file.name}")
                            else:
                                # Otherwise, treat it as a system/rule file and store it
                                if uploaded_file.name not in st.session_state.loaded_rules:
                                    content = uploaded_file.getvalue().decode('utf-8')
                                    # Update session and config to persist the file
                                    st.session_state.loaded_rules[uploaded_file.name] = content
                                    st.session_state.config['saved_rules'][uploaded_file.name] = content
                                    self.save_config(st.session_state.config)
                                    logger.info(f"Successfully loaded rule file: {uploaded_file.name} ({len(content)} bytes)")
                                    st.success(f"Rule file loaded: {uploaded_file.name}")
                                else:
                                    logger.info(f"Rule file already loaded, skipping: {uploaded_file.name}")
                        except Exception as e:
                            logger.error(f"Error processing system file {uploaded_file.name}: {str(e)}")
                            st.error(f"Failed to process file: {uploaded_file.name}")

            # Files tab - placeholder for ignore tree
            with files_tab:
                if repo_path and Path(repo_path).exists():
                    from frontend.components.ignore_tree import IgnoreTreeComponent

                    # Only reinitialize crawler if repo path or config changes
                    config_hash = str(hash(str(st.session_state.config)))
                    if ('crawler' not in st.session_state or
                        'config_hash' not in st.session_state or
                        st.session_state.config_hash != config_hash):
                        from backend.core.crawler import RepositoryCrawler
                        logger.info("Initializing new crawler")
                        repo_path = st.session_state.config.get('path', '')
                        st.session_state.crawler = RepositoryCrawler(repo_path, st.session_state.config)
                        st.session_state.config_hash = config_hash

                    # Get file tree and render ignore tree
                    file_tree = st.session_state.crawler.get_file_tree()
                    ignore_tree = IgnoreTreeComponent(file_tree)
                    ignore_tree.render()
                else:
                    st.info("Please enter a valid repository path in the Settings tab to manage ignore patterns.")

            return st.session_state.config.get('path', '')