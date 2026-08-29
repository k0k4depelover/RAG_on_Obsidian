from collections.abc import Iterator
from pathlib import Path
from typing import List


def walk_vault(
    vault_path: Path,
    include_dirs: List[str] | None = None,
    exclude_dirs: List[str] | None = None,
) -> Iterator[Path]:

    exclude_dirs = set(exclude_dirs) if exclude_dirs else set()
    include_dirs = set(include_dirs) if include_dirs else set()

    for file_path in vault_path.rglob("*.md"):

        rel_path = file_path.relative_to(vault_path)

        if any(part.startswith(".") for part in rel_path.parts[:-1]):
            continue

        if any(part in exclude_dirs for part in rel_path.parts[:-1]):
            continue

        if include_dirs:
            if not any(part in include_dirs for part in rel_path.parts[:-1]):
                continue

        yield file_path
