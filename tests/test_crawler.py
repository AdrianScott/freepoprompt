import pytest
from pathlib import Path
from backend.core.crawler import RepositoryCrawler

def test_ignore_patterns():
    """Test that ignore patterns are correctly applied."""
    # Create test config
    config = {
        'ignore_patterns': {
            'directories': ['.git', 'node_modules', '__pycache__'],
            'files': ['*.pyc', '*.log', '.env']
        }
    }
    
    # Initialize crawler with test config
    crawler = RepositoryCrawler(str(Path.cwd()), config)
    
    # Test directory ignore patterns
    assert crawler._should_ignore_dir('.git') == True
    assert crawler._should_ignore_dir('node_modules') == True
    assert crawler._should_ignore_dir('src') == False
    
    # Test file ignore patterns
    assert crawler._should_ignore_file('test.pyc') == True
    assert crawler._should_ignore_file('app.log') == True
    assert crawler._should_ignore_file('.env') == True
    assert crawler._should_ignore_file('main.py') == False
    
    # Get file tree and verify ignored items are not included
    tree = crawler.get_file_tree()
    
    def check_tree(tree_dict):
        """Recursively check tree for ignored items."""
        for name, contents in tree_dict.items():
            # Check that no ignored directories are present
            assert name not in config['ignore_patterns']['directories']
            
            # Check that no ignored files are present
            for pattern in config['ignore_patterns']['files']:
                if '*' in pattern:
                    pattern = pattern.replace('*', '')
                    assert not name.endswith(pattern)
                else:
                    assert name != pattern
            
            # Recursively check subdirectories
            if isinstance(contents, dict):
                check_tree(contents)
    
    # Check the contents of the tree
    if 'contents' in tree:
        check_tree(tree['contents'])

@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository structure."""
    # Create test files and directories
    (tmp_path / "file1.txt").write_text("test1")
    (tmp_path / "file2.py").write_text("test2")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("test3")
    (subdir / "file4.py").write_text("test4")
    
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "file5.txt").write_text("test5")
    
    return tmp_path

@pytest.fixture
def config():
    """Create a test configuration."""
    return {
        'ignore_patterns': {
            'directories': ['.git', '__pycache__'],
            'files': ['*.pyc', '*.log']
        }
    }

def test_file_tree_structure(test_repo, config):
    """Test that the file tree is built correctly."""
    crawler = RepositoryCrawler(test_repo, config)
    tree = crawler.get_file_tree()
    
    # Check root node
    assert tree['path'] == str(test_repo)
    assert tree['type'] == 'directory'
    assert 'children' in tree
    
    # Helper function to find a node by name
    def find_node(nodes, name):
        for node in nodes:
            if Path(node['path']).name == name:
                return node
        return None
    
    # Check root level files
    root_children = tree['children']
    file1 = find_node(root_children, 'file1.txt')
    assert file1 is not None
    assert file1['type'] == 'file'
    
    file2 = find_node(root_children, 'file2.py')
    assert file2 is not None
    assert file2['type'] == 'file'
    
    # Check subdirectory
    subdir = find_node(root_children, 'subdir')
    assert subdir is not None
    assert subdir['type'] == 'directory'
    assert 'children' in subdir
    
    # Check subdir files
    subdir_children = subdir['children']
    file3 = find_node(subdir_children, 'file3.txt')
    assert file3 is not None
    assert file3['type'] == 'file'
    
    file4 = find_node(subdir_children, 'file4.py')
    assert file4 is not None
    assert file4['type'] == 'file'
    
    # Check nested directory
    nested = find_node(subdir_children, 'nested')
    assert nested is not None
    assert nested['type'] == 'directory'
    assert 'children' in nested
    
    # Check nested file
    nested_children = nested['children']
    file5 = find_node(nested_children, 'file5.txt')
    assert file5 is not None
    assert file5['type'] == 'file'

def test_ignore_patterns(test_repo, config):
    """Test that ignore patterns are respected."""
    # Create some files that should be ignored
    (test_repo / "test.pyc").write_text("should be ignored")
    (test_repo / "test.log").write_text("should be ignored")
    (test_repo / ".git").mkdir()
    (test_repo / ".git" / "config").write_text("git config")
    
    crawler = RepositoryCrawler(test_repo, config)
    tree = crawler.get_file_tree()
    
    # Helper function to find all paths in tree
    def get_all_paths(node):
        paths = []
        if node['type'] == 'file':
            paths.append(node['path'])
        elif node['type'] == 'directory':
            paths.append(node['path'])
            for child in node.get('children', []):
                paths.extend(get_all_paths(child))
        return paths
    
    all_paths = get_all_paths(tree)
    
    # Check that ignored files are not in the tree
    assert not any('test.pyc' in path for path in all_paths)
    assert not any('test.log' in path for path in all_paths)
    assert not any('.git' in path for path in all_paths)

def test_empty_directory(tmp_path, config):
    """Test handling of empty directories."""
    crawler = RepositoryCrawler(tmp_path, config)
    tree = crawler.get_file_tree()
    
    assert tree['path'] == str(tmp_path)
    assert tree['type'] == 'directory'
    assert tree['children'] == []

def test_nonexistent_directory(tmp_path, config):
    """Test handling of nonexistent directories."""
    nonexistent = tmp_path / "nonexistent"
    crawler = RepositoryCrawler(nonexistent, config)
    
    # Should not raise an error due to allow_nonexistent=True
    tree = crawler.get_file_tree()
    
    assert tree['path'] == str(nonexistent)
    assert tree['type'] == 'directory'
    assert tree['children'] == []