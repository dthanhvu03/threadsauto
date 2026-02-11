#!/usr/bin/env python3
"""
Unit tests for git_cli.py

Tests cover:
- Branch name formatting
- Branch creation logic
- Validation functions
- Error handling
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cli.git_cli import GitCLI


class TestBranchNameFormatting:
    """Test branch name formatting and sanitization."""
    
    def test_format_feature_branch(self):
        """Test formatting feature branch."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'add new feature')
        assert result == 'feature/add-new-feature'
    
    def test_format_fix_branch(self):
        """Test formatting fix branch."""
        cli = GitCLI()
        result = cli._format_branch_name('fix', 'login bug')
        assert result == 'fix/login-bug'
    
    def test_sanitize_spaces(self):
        """Test space to hyphen conversion."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'my new feature')
        assert result == 'feature/my-new-feature'
    
    def test_sanitize_underscores(self):
        """Test underscore to hyphen conversion."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'my_new_feature')
        assert result == 'feature/my-new-feature'
    
    def test_sanitize_special_chars(self):
        """Test special character removal."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'add@feature#123!')
        assert result == 'feature/addfeature123'
    
    def test_sanitize_consecutive_hyphens(self):
        """Test consecutive hyphen removal."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'test---feature')
        assert result == 'feature/test-feature'
    
    def test_sanitize_leading_trailing_hyphens(self):
        """Test leading/trailing hyphen removal."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', '-test-feature-')
        assert result == 'feature/test-feature'
    
    def test_lowercase_conversion(self):
        """Test lowercase conversion."""
        cli = GitCLI()
        result = cli._format_branch_name('FEATURE', 'MY FEATURE')
        assert result == 'feature/my-feature'
    
    def test_max_length_enforcement(self):
        """Test max length enforcement."""
        cli = GitCLI()
        long_desc = 'a' * 100
        result = cli._format_branch_name('feature', long_desc)
        assert len(result.split('/')[1]) <= 50
    
    def test_invalid_branch_type(self):
        """Test invalid branch type rejection."""
        cli = GitCLI()
        with pytest.raises(ValueError, match='Invalid branch type'):
            cli._format_branch_name('invalid', 'test')
    
    def test_empty_description(self):
        """Test empty description rejection."""
        cli = GitCLI()
        with pytest.raises(ValueError, match='cannot be empty'):
            cli._format_branch_name('feature', '')
    
    def test_whitespace_only_description(self):
        """Test whitespace-only description rejection."""
        cli = GitCLI()
        with pytest.raises(ValueError, match='cannot be empty'):
            cli._format_branch_name('feature', '   ')
    
    def test_invalid_characters_after_sanitization(self):
        """Test description that becomes empty after sanitization."""
        cli = GitCLI()
        with pytest.raises(ValueError, match='becomes empty after sanitization'):
            cli._format_branch_name('feature', '@#$%^&*()')
    
    def test_all_branch_types(self):
        """Test all valid branch types."""
        cli = GitCLI()
        types = ['feature', 'fix', 'refactor', 'test', 'docs']
        for branch_type in types:
            result = cli._format_branch_name(branch_type, 'test')
            assert result.startswith(f'{branch_type}/')
            assert 'test' in result


class TestCreateBranch:
    """Test branch creation logic."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=temp_dir, check=True)
        
        # Create initial commit
        (repo_path / 'README.md').write_text('# Test')
        subprocess.run(['git', 'add', 'README.md'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=temp_dir, check=True, capture_output=True)
        
        yield repo_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_create_branch_success(self, temp_repo):
        """Test successful branch creation."""
        cli = GitCLI(repo_path=temp_repo)
        branch_name = cli.create_branch('feature', 'test feature', checkout=False)
        assert branch_name == 'feature/test-feature'
        
        # Verify branch exists
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert branch_name in result.stdout
    
    def test_create_branch_with_checkout(self, temp_repo):
        """Test branch creation with checkout."""
        cli = GitCLI(repo_path=temp_repo)
        branch_name = cli.create_branch('feature', 'test feature', checkout=True)
        
        # Verify we're on the new branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == branch_name
    
    def test_create_branch_from_specific_branch(self, temp_repo):
        """Test creating branch from specific source branch."""
        cli = GitCLI(repo_path=temp_repo)
        
        # Create source branch
        subprocess.run(['git', 'checkout', '-b', 'source'], cwd=temp_repo, check=True)
        
        branch_name = cli.create_branch(
            'feature', 
            'test feature', 
            checkout=False,
            from_branch='source'
        )
        
        # Verify branch exists
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert branch_name in result.stdout
    
    def test_create_branch_already_exists(self, temp_repo):
        """Test error when branch already exists."""
        cli = GitCLI(repo_path=temp_repo)
        
        # Create branch first
        cli.create_branch('feature', 'test feature', checkout=False)
        
        # Try to create again
        with pytest.raises(ValueError, match='already exists'):
            cli.create_branch('feature', 'test feature', checkout=False)
    
    def test_create_branch_invalid_source(self, temp_repo):
        """Test error when source branch doesn't exist."""
        cli = GitCLI(repo_path=temp_repo)
        
        with pytest.raises(ValueError, match='does not exist'):
            cli.create_branch(
                'feature',
                'test feature',
                checkout=False,
                from_branch='nonexistent'
            )
    
    def test_create_branch_no_git_repo(self, tmp_path):
        """Test error when not in git repository."""
        cli = GitCLI(repo_path=tmp_path)
        
        with pytest.raises(ValueError, match='Không phải git repository'):
            cli.create_branch('feature', 'test feature')


class TestGitCLIValidation:
    """Test validation and error handling."""
    
    def test_branch_type_case_insensitive(self):
        """Test branch type is case insensitive."""
        cli = GitCLI()
        result1 = cli._format_branch_name('FEATURE', 'test')
        result2 = cli._format_branch_name('feature', 'test')
        assert result1 == result2
    
    def test_description_trimming(self):
        """Test description whitespace trimming."""
        cli = GitCLI()
        result1 = cli._format_branch_name('feature', '  test  ')
        result2 = cli._format_branch_name('feature', 'test')
        assert result1 == result2
    
    @patch('scripts.cli.git_cli.subprocess.run')
    def test_git_command_error_handling(self, mock_run):
        """Test git command error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='Error')
        
        cli = GitCLI()
        with pytest.raises(subprocess.CalledProcessError):
            cli._run_git_command(['status'])


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_vietnamese_characters(self):
        """Test handling of Vietnamese characters."""
        cli = GitCLI()
        # Vietnamese characters should be removed
        result = cli._format_branch_name('feature', 'thêm tính năng mới')
        # Should only contain alphanumeric and hyphens
        assert all(c.isalnum() or c == '-' or c == '/' for c in result)
    
    def test_numbers_in_description(self):
        """Test numbers in description."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'feature v2.0')
        assert '2' in result and '0' in result
    
    def test_dots_in_description(self):
        """Test dots in description (allowed)."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'version 2.0')
        assert '.' in result
    
    def test_multiple_words(self):
        """Test multiple words in description."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'add user authentication system')
        assert result == 'feature/add-user-authentication-system'
    
    def test_single_word(self):
        """Test single word description."""
        cli = GitCLI()
        result = cli._format_branch_name('feature', 'auth')
        assert result == 'feature/auth'
