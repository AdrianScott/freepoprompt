import streamlit as st
import yaml
from pathlib import Path
import logging
import sys
from typing import Dict, Any
from threading import Lock

# Configure logging to also output to stdout
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
                'saved_rules': {}  # New field to store rules
            }
            self.initialize_state()
            self._initialized = True

    def initialize_state(self):
        """Initialize session state for sidebar with proper locking."""
        try:
            with self._config_lock:
                # First load config
                if 'config' not in st.session_state:
                    loaded_config = self.load_config()
                    if loaded_config:
                        st.session_state.config = loaded_config
                    else:
                        st.session_state.config = self.default_config.copy()
                        logger.info("No config file found, using defaults")

                # Ensure saved_rules exists in config
                if 'saved_rules' not in st.session_state.config:
                    st.session_state.config['saved_rules'] = {}

                # Initialize loaded_rules from config's saved_rules
                if 'loaded_rules' not in st.session_state:
                    st.session_state.loaded_rules = {}
                if 'creating_new_rule' not in st.session_state:
                    st.session_state.creating_new_rule = False
                if 'new_rule_name' not in st.session_state:
                    st.session_state.new_rule_name = ""
                if 'new_rule_content' not in st.session_state:
                    st.session_state.new_rule_content = ""

                # Load saved rules into loaded_rules
                if 'saved_rules' in st.session_state.config:
                    st.session_state.loaded_rules.update(st.session_state.config['saved_rules'])

                # Initialize other state
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
        # import pdb; pdb.set_trace()  # Breakpoint
        config_dir = Path('config')
        print(f"DEBUG: Looking for config directory at: {config_dir.absolute()}")
        logger.info(f"Looking for config directory at: {config_dir.absolute()}")
        print(f"DEBUG: Directory exists: {config_dir.exists()}")
        logger.info(f"Directory exists: {config_dir.exists()}")
        if config_dir.exists():
            contents = list(config_dir.iterdir())
            print(f"DEBUG: Config directory contents: {contents}")
            logger.info(f"Config directory contents: {contents}")

        config_path = config_dir / 'config.yaml'
        print(f"DEBUG: Looking for config file at: {config_path.absolute()}")
        logger.info(f"Looking for config file at: {config_path.absolute()}")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    print(f"DEBUG: Loaded config: {loaded_config}")
                    logger.info(f"Loaded config: {loaded_config}")
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
        """Save configuration to config.yaml with proper locking."""
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
        """Load configuration from uploaded file."""
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
        """Clear all sidebar-related state."""
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

    def _render_rules_tab(self):
        """Render the rules management tab."""
        st.markdown("### Rule Management")

        # Add new rule button
        if st.button("Create New Rule", key="create_new_rule"):
            if 'new_rule_name' not in st.session_state:
                st.session_state.new_rule_name = ""
            if 'new_rule_content' not in st.session_state:
                st.session_state.new_rule_content = ""
            st.session_state.creating_new_rule = True

        # New rule creation form
        if st.session_state.get('creating_new_rule', False):
            st.markdown("#### Create New Rule")
            new_rule_name = st.text_input("Rule Name",
                                        value=st.session_state.new_rule_name,
                                        key="new_rule_name_input",
                                        help="Enter a name for your rule (e.g. my_rule.cursorrules)")
            new_rule_content = st.text_area("Rule Content",
                                          value=st.session_state.new_rule_content,
                                          key="new_rule_content_input",
                                          height=200,
                                          help="Enter the content of your rule")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Save Rule", key="save_new_rule"):
                    if new_rule_name and new_rule_content:
                        # Save rule to config
                        st.session_state.config.setdefault('saved_rules', {})
                        st.session_state.config['saved_rules'][new_rule_name] = new_rule_content
                        # Update loaded rules
                        st.session_state.loaded_rules[new_rule_name] = new_rule_content
                        # Save config
                        self.save_config(st.session_state.config)
                        # Clear form
                        st.session_state.creating_new_rule = False
                        st.session_state.new_rule_name = ""
                        st.session_state.new_rule_content = ""
                        st.rerun()
            with col2:
                if st.button("Cancel", key="cancel_new_rule"):
                    st.session_state.creating_new_rule = False
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
                    st.code(rule_content)
                    if st.button("Delete Rule", key=f"delete_{rule_name}"):
                        # Remove from loaded rules
                        del st.session_state.loaded_rules[rule_name]
                        # Remove from config
                        if rule_name in st.session_state.config.get('saved_rules', {}):
                            del st.session_state.config['saved_rules'][rule_name]
                            self.save_config(st.session_state.config)
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
                help="Example: node_modules, .git, __pycache__"
            )
            
            # File patterns
            st.write("File Patterns")
            file_patterns = st.text_area(
                "Enter file patterns to ignore (one per line)",
                value="\n".join(st.session_state.config.get('ignore_patterns', {}).get('files', [])),
                help="Example: *.pyc, *.log, .env"
            )
            
            # Update button
            if st.button("Update Ignore Patterns"):
                # Parse patterns
                dir_list = [p.strip() for p in dir_patterns.split('\n') if p.strip()]
                file_list = [p.strip() for p in file_patterns.split('\n') if p.strip()]
                
                # Update config
                st.session_state.config['ignore_patterns'] = {
                    'directories': dir_list,
                    'files': file_list
                }
                self.save_config(st.session_state.config)
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
            st.title("File Prep")

            # Create tabs for different settings
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

            # Rules tab
            with rules_tab:
                self._render_rules_tab()

            # Files tab
            with files_tab:
                self._render_files_tab()

            return st.session_state.config.get('path', '')