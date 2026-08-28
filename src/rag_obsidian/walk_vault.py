import os
from pathlib import Path
from typing import List, Optional


def walk_vault(
    valt_path: str,
    include_dirs: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
):

    vault_root = Path(valt_path).resolve()

    exclude_set = set(exclude_dirs) if exclude_dirs else set()
    include_set = set(include_dirs) if include_dirs else set()

    for root, dirs, files in os.walk(vault_root):
        current_dir = Path(root)

        rel_path = current_dir.relative_to(vault_root)

        dirs[:] = [d for d in dirs if d.startswith(".") and d not in exclude_set]

        if include_set:
            parts = set(rel_path.parts)
            if not parts.intersection(include_set) and rel_path != Path("."):
                continue

        for file in files:
            if file.endswith(".md"):
                yield current_dir / file
