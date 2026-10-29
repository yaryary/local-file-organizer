from pathlib import Path


def scan_directory(scan_root: Path, limit: int = 100) -> list[dict[str, str | int]]:
    """Collect metadata for eligible regular files directly inside scan_root.

    The maximum entry count is configurable through limit and defaults to 100.
    The limit must be a positive integer; booleans are not accepted.

    Every immediate directory entry counts toward this limit, including hidden
    entries, directories, symbolic links, and regular files, even if excluded
    from the returned records. Subdirectories are not scanned recursively.

    A directory containing exactly limit entries is allowed. If the entry count
    exceeds limit, raise ValueError without returning a partial inventory.

    Validate limit before directory enumeration. Reject symbolic-link roots
    and roots that do not exist or are not directories.

    Args:
        scan_root: Directory to scan.
        limit: Maximum number of immediate directory entries allowed.

    Returns:
        Metadata records for eligible regular files. Hidden entries, symbolic
        links, non-file entries, and files whose metadata cannot be read are
        skipped.

    Raises:
        TypeError: If limit is a boolean or is not an integer.
        ValueError: If limit is zero or negative, scan_root is a symbolic link,
            scan_root does not exist or is not a directory, or the directory
            contains more than limit entries.
        OSError: If a filesystem operation fails outside the per-file metadata
            error handler, including during directory enumeration.

    This limit bounds directory-entry processing. It does not enforce a timeout
    or provide a complete filesystem security guarantee.
    """

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError(
             "Limit must be a positive integer; booleans are not allowed"
        )

    if limit <= 0:
        raise ValueError("Limit must be greater than 0")

    if scan_root.is_symlink():
        raise ValueError("The scan folder must not be a symbolic link.")

    if not scan_root.is_dir():
        raise ValueError(
            f"Scan folder does not exist or is not a directory: {scan_root}"
        )

    files: list[dict[str, str | int]] = []
    entries: list[Path] = []
    count = 0

    for entry in scan_root.iterdir():
        count += 1
        if count > limit:
            raise ValueError(
                f"Scan directory exceeds the maximum allowed entry count of {limit}"
            )

        entries.append(entry)

    entries.sort()

    for entry in entries:
        if entry.name.startswith("."):
            print(f"Skipped hidden entry: {entry.name}")
            continue
        
        if entry.is_symlink():
            print(f"Skipped symbolic link: {entry.name}")
            continue
        
        if not entry.is_file(follow_symlinks=False):
            print(f"Skipped non-file entry: {entry.name}")
            continue
        
        try:
            file_stat = entry.stat(follow_symlinks=False)
        except OSError as exc:
            print(f"Skipped unreadable metadata: {entry.name} ({exc})")
            continue
        
        file_record: dict[str, str | int] = {
            "name": entry.name,
            "extension": entry.suffix.lower(),
            "size_bytes": file_stat.st_size,
            "relative_path": entry.relative_to(scan_root).as_posix(),
            "modified_time_ns": file_stat.st_mtime_ns,
        }
        
        files.append(file_record) 

    return files


def main() -> None:
    project_dir = Path(__file__).parent
    scan_root = project_dir / "sandbox" / "input"

    try:
        print(f"Inspecting: {scan_root}")
        files = scan_directory(scan_root)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Error: {exc}")
        return

    print(f"\nCollected {len(files)} file records:")

    for file_record in files:
        print(file_record)


if __name__ == "__main__":
    main()