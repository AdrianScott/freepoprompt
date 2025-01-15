# Cross-platform Freepoprompt for use w/ o1-pro

This is a streamlined "Repoprompt" tool. You can use this with o1-pro or o1 to have it add new features to an existing codebase, and then use o1-xml-parser to update the files.
I've worked on this to generate input prompts to feed into o1-pro (or o1), and then use my version of McKay Wrigley's o1-xml-parser to parse the XML output and update local
files. By default, This repo has file-writing turned off by default, since we use the o1-xml-parser to update the files. I've sought to trim this down to only what's needed for
o1-pro and o1-xml-parser to work.

This is forked from Justin Lietz's original project: https://github.com/justinlietz93/RepoPrompt-Windows-Linux

From Justin: `Feel free to do whatever you want with this code, but please share it and feel free to give me credit. :) This project is still in progress. Most of the functionality works, but you may run into bugs and I have more features planned.`

The following docs may not be up to date:

# Repository Crawler 🔍

A powerful Python-based tool that quickly produces context prompts for LLMs by analyzing local repositories and generating structured documentation with token cost estimation. Built with Streamlit, it provides an intuitive web interface for exploring codebases and understanding their token usage in the context of AI language models.

## Features

### 🎯 Core Features

- Interactive repository exploration
- Token analysis with GPT model support
- Cross-platform compatibility
- Configurable ignore patterns
- XML-formatted codebase overview

### 🎨 Modern UI

- Tabbed sidebar interface for better organization
  - Settings: Model and repository configuration
  - Files: Upload and manage system files
  - Rules: Add rules and instruction files
  - Patterns: Configure ignore patterns
- Limited Visual file browser for repository selection
- File tree visualization
- Token analysis visualization

### 🔧 Configuration

- Extensive ignore patterns for files and directories
- Multiple GPT model support (TODO)
  - GPT-4 (default)
  - GPT-4-32k
  - GPT-3.5-turbo
  - GPT-3.5-turbo-16k
- Cross-platform path handling
- Configurable logging system

## Installation

1. Clone the repository:

```bash
git clone https://github.com/adrianscott/freepoprompt.git
cd freepoprompt
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
streamlit run main.py
```

2. Using the interface:
   - Select repository using the visual file browser
   - Configure ignore patterns if needed
   - Add rules/instruction files
   - Click "Generate Prompt" to analyze

## Configuration

### Repository Settings

- Use the Settings tab to:
  - Select token analysis model
  - Set repository path via browser or manual input

### File Management

- Use the Files tab to:
  - Upload configuration files (.yaml, .yml)
  - Upload rule files (.txt, .md, .cursorrules)
  - View and manage loaded files

### Pattern Management

- Use the Patterns tab to:
  - Configure ignored directories
  - Set ignored file patterns
  - Download current configuration

### Project Structure

```
Repository_Crawler/
├── frontend/          # UI components
├── backend/           # Core functionality
├── config/           # Configuration files
├── logs/            # Application logs
├── prompts/         # Generated output
└── tests/          # Test suite
```

## Known Issues

- Repository traversal system needs improvement
- XML generation formatting issues
- UI component state persistence
- Linux / Mac compatibility verification needed

## Next Steps

1. Fix repository traversal system
2. Improve XML generation
3. Enhance error handling
4. Add comprehensive testing
5. Test cross platform compatibility

## License

[MIT License](LICENSE)

## Support

For support, please open an issue in the GitHub repository.
