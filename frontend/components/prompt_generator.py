"""Component for generating prompts from selected files."""

import streamlit as st
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List
from backend.core.file_handler import FileHandler
from backend.core.crawler import RepositoryCrawler
from backend.core.tokenizer import TokenCalculator

logger = logging.getLogger(__name__)

class PromptGeneratorComponent:
    """Component for generating prompts from selected files."""
    
    def __init__(self, config: Dict[str, Any], file_handler: FileHandler):
        """Initialize the prompt generator component."""
        self.config = config
        self.file_handler = file_handler
        self.token_calculator = TokenCalculator()
        
    def _generate_file_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Generate a summary for a single file."""
        try:
            content = self.file_handler.read_file(file_path)
            if content is None:
                return None
                
            # Calculate tokens
            token_count, _ = self.token_calculator.count_tokens(content)
            
            return {
                'path': file_path,
                'content': content,
                'token_count': token_count
            }
            
        except Exception as e:
            logger.error(f"Error generating file summary: {str(e)}")
            return None
            
    def _generate_prompt(self, files: List[Dict[str, Any]], context: str) -> str:
        """Generate a prompt from the selected files and context."""
        try:
            prompt_parts = []
            
            # Add context if provided
            if context:
                prompt_parts.append(f"Context:\n{context}\n")
            
            # Add file contents
            for file_info in files:
                rel_path = Path(file_info['path']).name
                prompt_parts.append(f"\nFile: {rel_path}\n```\n{file_info['content']}\n```")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            return "Error generating prompt"
            
    def render(self) -> None:
        """Render the prompt generator component."""
        try:
            st.subheader("Generate Prompt")
            
            # Get selected file from session state
            selected_file = st.session_state.get('selected_file')
            if not selected_file:
                st.info("Select a file from the tree to generate a prompt")
                return
                
            # Generate file summary
            file_info = self._generate_file_summary(selected_file)
            if not file_info:
                st.error("Error reading selected file")
                return
                
            # Display file info
            st.markdown(f"**Selected File:** {Path(file_info['path']).name}")
            st.markdown(f"**Token Count:** {file_info['token_count']:,}")
            
            # Add context input
            context = st.text_area(
                "Additional Context",
                help="Add any additional context or instructions for the prompt"
            )
            
            # Generate button
            if st.button("Generate Prompt"):
                prompt = self._generate_prompt([file_info], context)
                
                # Show the generated prompt
                st.subheader("Generated Prompt")
                st.code(prompt, language="markdown")
                
                # Copy button
                if st.button("Copy to Clipboard"):
                    st.write("Prompt copied to clipboard!")
                    
        except Exception as e:
            logger.error(f"Error rendering prompt generator: {str(e)}")
            st.error("Error rendering prompt generator")

def render_prompt_generator(config: Dict[str, Any], file_handler: FileHandler, crawler: RepositoryCrawler) -> None:
    """Render the prompt generator component."""
    try:
        component = PromptGeneratorComponent(config, file_handler)
        component.render()
    except Exception as e:
        logger.error(f"Error rendering prompt generator: {str(e)}")
        st.error("Error rendering prompt generator")
