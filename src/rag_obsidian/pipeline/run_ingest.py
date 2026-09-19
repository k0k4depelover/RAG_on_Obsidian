"""
Se encarga de toda la parte de splitear los textos en base a los headers
previamente definidos en Obsidian, creando una jerarquia y asociando el texto a
la una jerarquia de archivo, ejemplo:

 ["ML > RNN", "Recursive Neural Network es un mecanismo que permite conectar la salida de una red neuronal a datos que envia"]

"""

import json
from dataclasses import asdict
from pathlib import Path

from rag_obsidian.auxiliars.split_by_headers import split_by_headers
from rag_obsidian.auxiliars.split_long_section import split_long_section
from rag_obsidian.auxiliars.walk_vault import walk_vault
from rag_obsidian.chunks import Chunk
from rag_obsidian.configuration.load_params import load_params

VAULT_PATH = Path("data/raw")
OUTPUT_PATH = Path("data/processed/chunks.jsonl")


def build_chunks(
    vault_path: Path, include_dirs, exclude_dirs, max_chars, overlap_chars
):
    for file_path in walk_vault(
        vault_path,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
    ):
        content = file_path.read_text(encoding="utf-8")
        rel_path = file_path.relative_to(vault_path)
        for header_path, section_text in split_by_headers(content):
            pieces = split_long_section(
                section_text, max_chars=max_chars, overlap_chars=overlap_chars
            )

            for i, piece in enumerate(pieces):
                yield Chunk(
                    text=piece,
                    source_path=str(rel_path),
                    note_title=file_path.stem,
                    header_path=header_path,
                    chunk_index=i,
                )


def main():
    params = load_params()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        for chunk in build_chunks(
            vault_path=VAULT_PATH,
            include_dirs=params.get("include_dirs"),
            exclude_dirs=params.get("exclude_dirs"),
            overlap_chars=params.get("overlap_chars"),
        ):
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
            total += 1
    print(f"[ingest] {total} chunks escritos en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
