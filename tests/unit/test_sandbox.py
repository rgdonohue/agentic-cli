"""Unit tests for file system sandbox - PoC 3."""

from pathlib import Path

import pytest

from agentic.sandbox import Sandbox, SandboxError, FileConflict


class TestSandbox:
    """Test sandbox directory management and file operations."""

    def test_sandbox_creates_preview_directory(self, temp_dir: Path) -> None:
        """Test that Sandbox creates .agentic/preview directory."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        Sandbox(project_dir)
        
        preview_dir = project_dir / ".agentic" / "preview"
        assert preview_dir.exists()
        assert preview_dir.is_dir()

    def test_sandbox_isolates_generated_files(self, temp_dir: Path) -> None:
        """Test that generated files only appear in preview directory."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        # Write a file to sandbox
        content = "print('Hello, World!')"
        sandbox.write_file("hello.py", content)
        
        # File should exist in preview but not in project root
        preview_file = project_dir / ".agentic" / "preview" / "hello.py"
        project_file = project_dir / "hello.py"
        
        assert preview_file.exists()
        assert preview_file.read_text() == content
        assert not project_file.exists()

    def test_sandbox_prevents_directory_traversal(self, temp_dir: Path) -> None:
        """Test that sandbox rejects dangerous file paths."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        dangerous_paths = [
            ("../../../etc/passwd", "Path traversal detected"),
            ("../../sensitive.txt", "Path traversal detected"),
            ("/etc/passwd", "Absolute paths not allowed"),
            ("~/secret.key", "Absolute paths not allowed"),
            ("..\\..\\windows\\system32\\config", "Path traversal detected")
        ]
        
        for path, expected_error in dangerous_paths:
            with pytest.raises(SandboxError, match=expected_error):
                sandbox.write_file(path, "malicious content")

    def test_sandbox_allows_safe_subdirectories(self, temp_dir: Path) -> None:
        """Test that sandbox allows creating files in safe subdirectories."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        safe_paths = [
            "src/main.py",
            "tests/test_main.py",
            "docs/README.md",
            "config/settings.yaml"
        ]
        
        for path in safe_paths:
            content = f"Content for {path}"
            sandbox.write_file(path, content)
            
            preview_file = project_dir / ".agentic" / "preview" / path
            assert preview_file.exists()
            assert preview_file.read_text() == content

    def test_sandbox_lists_pending_files(self, temp_dir: Path) -> None:
        """Test that sandbox can list all pending files."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        # Create several files
        files = {
            "main.py": "print('main')",
            "src/utils.py": "def helper(): pass",
            "tests/test_main.py": "def test_main(): pass"
        }
        
        for path, content in files.items():
            sandbox.write_file(path, content)
        
        pending_files = sandbox.list_pending_files()
        
        assert len(pending_files) == 3
        assert "main.py" in [f.relative_path for f in pending_files]
        assert "src/utils.py" in [f.relative_path for f in pending_files]
        assert "tests/test_main.py" in [f.relative_path for f in pending_files]

    def test_sandbox_detects_conflicts_with_existing_files(self, temp_dir: Path) -> None:
        """Test that sandbox detects conflicts with existing project files."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        # Create existing file in project
        existing_file = project_dir / "main.py"
        existing_file.write_text("# Existing content")
        
        sandbox = Sandbox(project_dir)
        
        # Try to write to same path
        sandbox.write_file("main.py", "# New content")
        
        conflicts = sandbox.detect_conflicts()
        
        assert len(conflicts) == 1
        assert conflicts[0].path == "main.py"
        assert conflicts[0].existing_content == "# Existing content"
        assert conflicts[0].new_content == "# New content"

    def test_sandbox_applies_changes_to_project(self, temp_dir: Path) -> None:
        """Test that apply moves files from preview to project."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        # Create files in sandbox
        files = {
            "main.py": "print('Hello')",
            "src/utils.py": "def helper(): pass"
        }
        
        for path, content in files.items():
            sandbox.write_file(path, content)
        
        # Apply changes
        applied_files = sandbox.apply_changes()
        
        # Files should now exist in project root
        assert len(applied_files) == 2
        assert (project_dir / "main.py").exists()
        assert (project_dir / "src" / "utils.py").exists()
        
        # Content should match
        assert (project_dir / "main.py").read_text() == "print('Hello')"
        assert (project_dir / "src" / "utils.py").read_text() == "def helper(): pass"
        
        # Preview directory should be cleaned up
        assert len(list(sandbox.list_pending_files())) == 0

    def test_sandbox_handles_apply_with_conflicts(self, temp_dir: Path) -> None:
        """Test that apply fails when conflicts exist without --force."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        # Create existing file
        existing_file = project_dir / "main.py"
        existing_file.write_text("# Original")
        
        sandbox = Sandbox(project_dir)
        sandbox.write_file("main.py", "# Modified")
        
        # Apply should fail due to conflict
        with pytest.raises(SandboxError, match="Conflicts detected"):
            sandbox.apply_changes()
        
        # Original file should be unchanged
        assert existing_file.read_text() == "# Original"

    def test_sandbox_allows_force_apply_with_conflicts(self, temp_dir: Path) -> None:
        """Test that apply works with --force flag even with conflicts."""
        project_dir = temp_dir / "project" 
        project_dir.mkdir()
        
        # Create existing file
        existing_file = project_dir / "main.py"
        existing_file.write_text("# Original")
        
        sandbox = Sandbox(project_dir)
        sandbox.write_file("main.py", "# Modified")
        
        # Force apply should work
        applied_files = sandbox.apply_changes(force=True)
        
        assert len(applied_files) == 1
        assert existing_file.read_text() == "# Modified"

    def test_sandbox_clears_preview_directory(self, temp_dir: Path) -> None:
        """Test that sandbox can clear all pending changes."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        # Create files
        sandbox.write_file("file1.py", "content1")
        sandbox.write_file("file2.py", "content2")
        
        assert len(sandbox.list_pending_files()) == 2
        
        # Clear preview
        sandbox.clear_preview()
        
        assert len(sandbox.list_pending_files()) == 0

    def test_sandbox_validates_file_paths(self, temp_dir: Path) -> None:
        """Test that sandbox validates file paths for safety."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        
        sandbox = Sandbox(project_dir)
        
        # Test invalid characters in filename
        with pytest.raises(SandboxError, match="Invalid characters in path"):
            sandbox.write_file("file<>:\"|.py", "content")
        
        # Test empty filename
        with pytest.raises(SandboxError, match="Empty path not allowed"):
            sandbox.write_file("", "content")
        
        # Test absolute path
        with pytest.raises(SandboxError, match="Absolute paths not allowed"):
            sandbox.write_file("/tmp/file.py", "content")


class TestFileConflict:
    """Test file conflict detection and resolution."""

    def test_file_conflict_creation(self) -> None:
        """Test FileConflict object creation and properties."""
        conflict = FileConflict(
            path="main.py",
            existing_content="# Original",
            new_content="# Modified"
        )
        
        assert conflict.path == "main.py"
        assert conflict.existing_content == "# Original"
        assert conflict.new_content == "# Modified"

    def test_file_conflict_diff_generation(self) -> None:
        """Test that FileConflict can generate diff output."""
        conflict = FileConflict(
            path="main.py",
            existing_content="line1\nline2\nline3",
            new_content="line1\nmodified line2\nline3"
        )
        
        diff = conflict.generate_diff()
        
        assert "main.py" in diff
        assert "-line2" in diff
        assert "+modified line2" in diff