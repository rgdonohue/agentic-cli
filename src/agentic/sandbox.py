"""File system sandbox for safe code generation and preview."""

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import difflib


class SandboxError(Exception):
    """Raised when sandbox operations fail."""
    pass


@dataclass
class PendingFile:
    """Represents a file pending application to the project."""
    
    relative_path: str
    content: str
    preview_path: Path
    target_path: Path


@dataclass
class FileConflict:
    """Represents a conflict between existing and new file content."""
    
    path: str
    existing_content: str
    new_content: str
    
    def generate_diff(self) -> str:
        """Generate a unified diff showing the conflict."""
        existing_lines = self.existing_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            existing_lines,
            new_lines,
            fromfile=f"a/{self.path}",
            tofile=f"b/{self.path}",
            lineterm=""
        )
        
        return "".join(diff)


class Sandbox:
    """Secure sandbox for isolating generated files before application."""
    
    def __init__(self, project_dir: Path):
        """Initialize sandbox for the given project directory."""
        self.project_dir = project_dir.resolve()
        self.agentic_dir = self.project_dir / ".agentic"
        self.preview_dir = self.agentic_dir / "preview"
        
        # Create sandbox directories
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure sandbox directories exist."""
        self.agentic_dir.mkdir(exist_ok=True)
        self.preview_dir.mkdir(exist_ok=True)
    
    def _validate_path(self, file_path: str) -> None:
        """Validate file path for security and safety."""
        if not file_path or file_path.strip() == "":
            raise SandboxError("Empty path not allowed")
        
        # Check for tilde expansion (home directory)
        if file_path.startswith("~"):
            raise SandboxError("Absolute paths not allowed")
        
        # Check for absolute paths
        if os.path.isabs(file_path):
            raise SandboxError("Absolute paths not allowed")
        
        # Check for directory traversal (both Unix and Windows style)
        if ".." in Path(file_path).parts:
            raise SandboxError("Path traversal detected")
        
        # Check for Windows-style directory traversal
        if "..\\" in file_path or "/../" in file_path:
            raise SandboxError("Path traversal detected")
        
        # Check for invalid characters (Windows and general safety)
        invalid_chars = r'[<>:"|?*\x00-\x1f]'
        if re.search(invalid_chars, file_path):
            raise SandboxError("Invalid characters in path")
        
        # Additional safety checks
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith(("/", "\\")):
            raise SandboxError("Path traversal detected")
    
    def write_file(self, file_path: str, content: str) -> None:
        """Write a file to the sandbox preview directory."""
        self._validate_path(file_path)
        
        # Create target path in preview directory
        preview_file = self.preview_dir / file_path
        
        # Ensure parent directories exist
        preview_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to preview file
        preview_file.write_text(content, encoding="utf-8")
    
    def list_pending_files(self) -> List[PendingFile]:
        """List all files pending application to the project."""
        pending_files = []
        
        if not self.preview_dir.exists():
            return pending_files
        
        # Walk through all files in preview directory
        for file_path in self.preview_dir.rglob("*"):
            if file_path.is_file():
                # Calculate relative path from preview directory
                relative_path = str(file_path.relative_to(self.preview_dir))
                
                # Read content
                content = file_path.read_text(encoding="utf-8")
                
                # Calculate target path in project
                target_path = self.project_dir / relative_path
                
                pending_file = PendingFile(
                    relative_path=relative_path,
                    content=content,
                    preview_path=file_path,
                    target_path=target_path
                )
                
                pending_files.append(pending_file)
        
        return pending_files
    
    def detect_conflicts(self) -> List[FileConflict]:
        """Detect conflicts between pending files and existing project files."""
        conflicts = []
        
        for pending_file in self.list_pending_files():
            if pending_file.target_path.exists():
                existing_content = pending_file.target_path.read_text(encoding="utf-8")
                
                # Only consider it a conflict if content differs
                if existing_content != pending_file.content:
                    conflict = FileConflict(
                        path=pending_file.relative_path,
                        existing_content=existing_content,
                        new_content=pending_file.content
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def apply_changes(self, force: bool = False) -> List[str]:
        """Apply pending changes to the project directory."""
        pending_files = self.list_pending_files()
        
        if not pending_files:
            return []
        
        # Check for conflicts unless force is specified
        if not force:
            conflicts = self.detect_conflicts()
            if conflicts:
                conflict_paths = [c.path for c in conflicts]
                raise SandboxError(
                    f"Conflicts detected in files: {', '.join(conflict_paths)}. Use --force to override."
                )
        
        applied_files = []
        
        for pending_file in pending_files:
            # Ensure target directory exists
            pending_file.target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file from preview to target location
            shutil.copy2(pending_file.preview_path, pending_file.target_path)
            
            applied_files.append(pending_file.relative_path)
        
        # Clear preview directory after successful application
        self.clear_preview()
        
        return applied_files
    
    def clear_preview(self) -> None:
        """Clear all files from the preview directory."""
        if self.preview_dir.exists():
            shutil.rmtree(self.preview_dir)
            self.preview_dir.mkdir(exist_ok=True)
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from the preview directory."""
        self._validate_path(file_path)
        
        preview_file = self.preview_dir / file_path
        if preview_file.exists() and preview_file.is_file():
            return preview_file.read_text(encoding="utf-8")
        
        return None
    
    def remove_file(self, file_path: str) -> bool:
        """Remove a file from the preview directory."""
        self._validate_path(file_path)
        
        preview_file = self.preview_dir / file_path
        if preview_file.exists() and preview_file.is_file():
            preview_file.unlink()
            
            # Remove empty parent directories
            try:
                parent = preview_file.parent
                while parent != self.preview_dir and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
            except OSError:
                # Directory not empty or other issue, ignore
                pass
            
            return True
        
        return False
    
    def get_preview_stats(self) -> dict:
        """Get statistics about the preview directory."""
        pending_files = self.list_pending_files()
        conflicts = self.detect_conflicts()
        
        total_size = sum(
            len(pf.content.encode('utf-8')) 
            for pf in pending_files
        )
        
        return {
            "pending_files": len(pending_files),
            "conflicts": len(conflicts),
            "total_size_bytes": total_size,
            "preview_directory": str(self.preview_dir)
        }