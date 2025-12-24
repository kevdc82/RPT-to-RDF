"""
File utility functions for RPT to RDF Converter.

Provides helper functions for file operations, path handling,
and file discovery.
"""

import re
import shutil
from pathlib import Path
from typing import Iterator, Optional, Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Path object for the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(name: str, replacement: str = "_") -> str:
    """Convert a string to a safe filename.

    Args:
        name: Original name.
        replacement: Character to replace unsafe characters with.

    Returns:
        Safe filename string.
    """
    # Remove or replace unsafe characters
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    safe_name = re.sub(unsafe_chars, replacement, name)

    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(". ")

    # Ensure name is not empty
    if not safe_name:
        safe_name = "unnamed"

    # Truncate if too long (Windows has 255 char limit)
    max_length = 200
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]

    return safe_name


def get_rpt_files(
    directory: Union[str, Path],
    recursive: bool = True,
    pattern: str = "*.rpt",
) -> Iterator[Path]:
    """Find all RPT files in a directory.

    Args:
        directory: Directory to search.
        recursive: Whether to search subdirectories.
        pattern: Glob pattern for files.

    Yields:
        Path objects for each RPT file found.
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return

    if not dir_path.is_dir():
        if dir_path.suffix.lower() == ".rpt":
            yield dir_path
        return

    if recursive:
        yield from dir_path.rglob(pattern)
    else:
        yield from dir_path.glob(pattern)


def get_output_path(
    input_file: Path,
    input_dir: Path,
    output_dir: Path,
    new_extension: str = ".rdf",
) -> Path:
    """Calculate output path preserving directory structure.

    Args:
        input_file: Input file path.
        input_dir: Base input directory.
        output_dir: Base output directory.
        new_extension: New file extension.

    Returns:
        Output file path.
    """
    # Get relative path from input directory
    try:
        relative_path = input_file.relative_to(input_dir)
    except ValueError:
        # File is not under input_dir, use just the filename
        relative_path = Path(input_file.name)

    # Create output path with new extension
    output_path = output_dir / relative_path.with_suffix(new_extension)

    return output_path


def backup_file(file_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
    """Create a backup of a file.

    Args:
        file_path: File to backup.
        backup_dir: Directory for backup. If None, backup in same directory.

    Returns:
        Path to backup file, or None if original doesn't exist.
    """
    if not file_path.exists():
        return None

    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{file_path.name}.bak"
    else:
        backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")

    shutil.copy2(file_path, backup_path)
    return backup_path


def clean_temp_files(temp_dir: Path, pattern: str = "*.xml") -> int:
    """Remove temporary files from a directory.

    Args:
        temp_dir: Temporary directory.
        pattern: Glob pattern for files to remove.

    Returns:
        Number of files removed.
    """
    if not temp_dir.exists():
        return 0

    count = 0
    for file_path in temp_dir.glob(pattern):
        try:
            file_path.unlink()
            count += 1
        except OSError:
            pass  # Ignore errors when deleting temp files

    return count


def get_file_info(file_path: Path) -> dict:
    """Get information about a file.

    Args:
        file_path: File path.

    Returns:
        Dictionary with file information.
    """
    if not file_path.exists():
        return {
            "exists": False,
            "path": str(file_path),
        }

    stat = file_path.stat()
    return {
        "exists": True,
        "path": str(file_path),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size": stat.st_size,
        "size_human": format_file_size(stat.st_size),
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string.
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def copy_with_structure(
    source_file: Path,
    source_base: Path,
    dest_base: Path,
) -> Path:
    """Copy a file preserving directory structure.

    Args:
        source_file: Source file path.
        source_base: Base directory of source.
        dest_base: Base directory of destination.

    Returns:
        Destination file path.
    """
    try:
        relative = source_file.relative_to(source_base)
    except ValueError:
        relative = Path(source_file.name)

    dest_file = dest_base / relative
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_file, dest_file)
    return dest_file
