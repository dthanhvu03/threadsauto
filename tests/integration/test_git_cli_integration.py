#!/usr/bin/env python3
"""
Integration tests for git_cli.py

Tests require actual git repository and may be slower.
Marked with @pytest.mark.integration
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cli.git_cli import GitCLI


@pytest.mark.integration
class TestGitCLIIntegration:
    """Integration tests for GitCLI."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, check=True)
        
        # Create initial commit
        (repo_path / 'README.md').write_text('# Test Repository')
        subprocess.run(['git', 'add', 'README.md'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=temp_dir, check=True, capture_output=True)
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.integration
    def test_full_branch_workflow(self, temp_repo):
        """Test complete branch creation and checkout workflow."""
        cli = GitCLI(repo_path=temp_repo)
        
        # Create branch
        branch_name = cli.create_branch('feature', 'new feature', checkout=True)
        assert branch_name == 'feature/new-feature'
        
        # Verify current branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == branch_name
        
        # Make a commit on new branch
        (temp_repo / 'new_file.txt').write_text('test')
        subprocess.run(['git', 'add', 'new_file.txt'], cwd=temp_repo, check=True)
        subprocess.run(['git', 'commit', '-m', 'Add new file'], cwd=temp_repo, check=True, capture_output=True)
        
        # Switch back to main
        subprocess.run(['git', 'checkout', 'main'], cwd=temp_repo, check=True)
        
        # Verify branch still exists
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert branch_name in result.stdout
    
    @pytest.mark.integration
    def test_branch_name_formatting_integration(self, temp_repo):
        """Test branch name formatting with actual git."""
        cli = GitCLI(repo_path=temp_repo)
        
        test_cases = [
            ('feature', 'add login', 'feature/add-login'),
            ('fix', 'bug #123', 'fix/bug-123'),
            ('refactor', 'clean up code', 'refactor/clean-up-code'),
            ('test', 'add unit tests', 'test/add-unit-tests'),
            ('docs', 'update README', 'docs/update-readme'),
        ]
        
        for branch_type, description, expected in test_cases:
            branch_name = cli.create_branch(branch_type, description, checkout=False)
            assert branch_name == expected
            
            # Verify branch exists in git
            result = subprocess.run(
                ['git', 'branch', '--list', branch_name],
                cwd=temp_repo,
                capture_output=True,
                text=True
            )
            assert branch_name in result.stdout
            
            # Delete branch for next test
            subprocess.run(['git', 'branch', '-D', branch_name], cwd=temp_repo, check=True, capture_output=True)
