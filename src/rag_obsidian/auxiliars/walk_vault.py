from collections.abc import Iterator
from pathlib import Path
from typing import List

"""
    Funcion para recorrer el vault de Obsidian, toma la ruta de tipo Path,
    y parametros como directorios a incluir y directorios a excluir, retornando
    un iterador de las rutas.

    Primero define un array (set) con la lista de archivos incluidos implicitamente y
    excluidos.

    Recorre todos los archivos con terminacion '.md' y ajusta la ruta a una relativa.

    Posteriormente realiza validaciones, si el archivo inicia con '.' lo ignora.

    Valida si esta en exclude_dirs para ignorarlo.


"""


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
