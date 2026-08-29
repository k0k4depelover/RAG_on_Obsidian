from dataclasses import is_dataclass

import pytest

from rag_obsidian.chunks import Chunk
from rag_obsidian.walk_vault import walk_vault

# TEST UNITARIO


def test_chunk_dataclass_instantiation():
    chunk = Chunk(
        text="Contenido de prueba",
        source_path="notas/ejemplo.md",
        note_title="Ejemplo",
        header_path="Introducción > Subsección",
    )
    assert is_dataclass(chunk)
    assert chunk.text == "Contenido de prueba"
    assert chunk.tags == []
    assert chunk.chunk_index == 0


@pytest.fixture
def mock_vault(tmp_path):
    """
    Crea una estructura de carpetas simulada en un directorio temporal:

    vault/
    ├── nota1.md
    ├── .obsidian/
    │   └── config.md (debe ignorarse por oculto)
    ├── oculto_excluido/
    │   └── nota_privada.md (debe ignorarse por exclude_dirs)
    ├── proyectos/
    │   └── proyecto1.md
    └── archivo.txt (debe ignorarse por no ser .md)
    """
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()

    (vault_dir / "nota1.md").write_text("# Nota 1")

    (vault_dir / "nota2.txt").write_text("Nota 2")

    dot_dir = vault_dir / ".obsidian"
    dot_dir.mkdir()
    (dot_dir / "config.md").write_text("config")

    ex_dir = vault_dir / "oculto_excluido"
    ex_dir.mkdir()
    (ex_dir / "nota_privada.md").write_text("# Privado")

    proj_dir = vault_dir / "project_dir"
    proj_dir.mkdir()
    (proj_dir / "Ejemplo.md").write_text("# Bases de Datos")

    return vault_dir


def test_walk_vault_basic_traversal_and_filters(mock_vault):
    found_files = list(walk_vault(mock_vault, exclude_dirs=["oculto_excluido"]))
    found_names = [f for f in found_files]

    assert "nota1.md" in found_names
    assert "nota2.txt" not in found_names
    assert "config.md" not in found_names
    assert "nota_privada.md" not in found_names
    assert "Ejemplo.md" in found_names
    assert len(found_files) == 2


def test_walk_vault_include_dirs_filter(mock_vault):
    found_files = list(walk_vault(mock_vault, include_dirs=["project_dir"]))

    found_files = [f for f in found_files]

    assert "Ejemplo.md" in found_files
    assert "nota1.md" not in found_files
    assert len(found_files) == 1


def test_integration_walk_and_chunk_creation(mock_vault):
    chunks = []

    for file_path in walk_vault(mock_vault):
        content = file_path.read_text(encoding="utf-8")

        chunk = Chunk(
            text=content,
            source_path=str(file_path),
            note_title=file_path.stem,
            header_path=file_path.name,
        )
        chunks.append(chunk)

    assert len(chunks) >= 2
    assert all(isinstance(c, Chunk) for c in chunks)
    assert any(c.note_title == "proyecto1" for c in chunks)
