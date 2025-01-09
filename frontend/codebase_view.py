"""Component for displaying the codebase view."""

import streamlit as st
import yaml
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenCalculator
from frontend.home import render_token_analysis

logger = logging.getLogger(__name__)

def get_file_contents(file_path: str) -> Optional[str]:
    """Read and return file contents safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def process_tree(node: Dict[str, Any], file_handler: FileHandler) -> List[Dict[str, Any]]:
    """Process a file tree node and return file information."""
    files_info = []
    
    try:
        # Get path and type from node
        path = node.get('path')
        node_type = node.get('type')
        
        if not path or not node_type:
            logger.error(f"Invalid node format: missing path or type: {node}")
            return files_info
            
        if node_type == 'file':
            # Process file
            content = file_handler.read_file(path)
            if content is not None:
                files_info.append({
                    'path': path,
                    'content': content,
                    'type': 'file'
                })
        elif node_type == 'directory':
            # Process directory children
            for child in node.get('children', []):
                files_info.extend(process_tree(child, file_handler))
                
    except Exception as e:
        logger.error(f"Error processing tree node: {str(e)}")
        
    return files_info

def analyze_codebase(repo_path: str, file_handler: FileHandler, file_tree: Dict[str, Any]) -> Optional[str]:
    """Analyze the codebase and generate an overview."""
    try:
        # Process the file tree
        files_info = process_tree(file_tree, file_handler)
        
        if not files_info:
            return None
            
        # Build overview
        overview = []
        
        # Add repository information
        overview.append(f"Repository Path: {repo_path}")
        overview.append(f"Total Files: {len(files_info)}")
        overview.append("")
        
        # Add file information
        for file_info in files_info:
            file_path = file_info['path']
            content = file_info.get('content', '')
            
            overview.append(f"File: {file_path}")
            overview.append(f"Size: {len(content)} bytes")
            overview.append("---")
            overview.append(content)
            overview.append("")
            
        return "\n".join(overview)
        
    except Exception as e:
        logger.error(f"Error generating codebase overview: {str(e)}")
        return None

def build_prompt(repo_path: str, file_tree: Dict[str, Any], file_handler: FileHandler) -> str:
    """Build a formatted prompt from the codebase contents."""
    try:
        # Process the file tree
        files_info = process_tree(file_tree, file_handler)
        
        # Build prompt
        prompt_parts = []
        
        # Get path style from config
        use_relative_paths = st.session_state.config.get('use_relative_paths', True)
        repo_name = Path(repo_path).name
        
        # Add repository information
        prompt_parts.append("<repository>")
        prompt_parts.append(f"<name>{repo_name}</name>")
        prompt_parts.append(f"<file_count>{len(files_info)}</file_count>")
        
        # Add loaded rules if any
        if hasattr(st.session_state, 'loaded_rules') and st.session_state.loaded_rules:
            prompt_parts.append("<rules>")
            for rule_name, rule_content in st.session_state.loaded_rules.items():
                prompt_parts.append(f"<rule name='{rule_name}'>")
                prompt_parts.append("<![CDATA[")
                prompt_parts.append(rule_content)
                prompt_parts.append("]]>")
                prompt_parts.append("</rule>")
            prompt_parts.append("</rules>")
        
        # Add file contents in XML format
        prompt_parts.append("<files>")
        for file_info in files_info:
            abs_path = Path(file_info['path'])
            if use_relative_paths:
                # Use repository-relative path: "reponame/path/to/file"
                file_path = f"{repo_name}/{abs_path.relative_to(repo_path)}"
            else:
                # Use absolute path
                file_path = str(abs_path)
            
            content = file_info.get('content', '')
            
            prompt_parts.append(f"<file path='{file_path}'>")
            prompt_parts.append("<![CDATA[")
            prompt_parts.append(content)
            prompt_parts.append("]]>")
            prompt_parts.append("</file>")
            
        prompt_parts.append("</files>")
        prompt_parts.append("</repository>")
        
        return "\n".join(prompt_parts)
        
    except Exception as e:
        logger.error(f"Error building prompt: {str(e)}")
        return ""

def render_codebase_view(file_handler: FileHandler, crawler: RepositoryCrawler):
    """Render the codebase view page."""
    st.title("Codebase Parser ")
    
    # Get repository path from config
    repo_path = st.session_state.config.get('path', '')
    if not repo_path:
        st.warning("No repository path configured.")
        return
    
    if st.button("Generate Prompt"):
        with st.spinner("Analyzing codebase..."):
            try:
                # Get file tree from crawler
                file_tree = crawler.get_file_tree()
                
                # Create tabs for different views
                overview_tab, prompt_tab, tokens_tab = st.tabs([
                    "Overview", 
                    "Generated Prompt",
                    "Token Analysis"
                ])
                
                with overview_tab:
                    # Analyze codebase
                    overview = analyze_codebase(repo_path, file_handler, file_tree)
                    if overview is None:
                        st.error("Failed to analyze codebase")
                        return
                    st.code(overview, language="markdown")
                
                with prompt_tab:
                    # Build prompt
                    prompt = build_prompt(repo_path, file_tree, file_handler)
                    st.code(prompt, language="xml")
                
                with tokens_tab:
                    # Convert tree to string for token analysis
                    tree_str = yaml.dump(file_tree, default_flow_style=False)
                    token_calculator = TokenCalculator()
                    render_token_analysis(tree_str, token_calculator, st.session_state.config.get('model', 'gpt-4'))
                
            except Exception as e:
                logger.error(f"Error generating codebase overview: {str(e)}")
                st.error(f"Error generating codebase overview: {str(e)}")

if __name__ == "__main__":
    render_codebase_view(FileHandler(), RepositoryCrawler())