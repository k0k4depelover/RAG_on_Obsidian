from dataclasses import is_dataclass

from ..rag_obsidian.chunks import Chunk

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
