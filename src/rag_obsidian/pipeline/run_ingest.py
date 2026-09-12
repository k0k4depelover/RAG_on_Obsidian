"""
Se encarga de toda la parte de splitear los textos en base a los headers
previamente definidos en Obsidian, creando una jerarquia y asociando el texto a
la una jerarquia de archivo, ejemplo:

 ["ML > RNN", "Recursive Neural Network es un mecanismo que permite conectar la salida de una red neuronal a datos que envia"]

"""

from pathlib import Path

import yaml

VAULT_PATH = Path("/home/oskar/Desktop/Obsidian-Vault")
OUTPUT_PATH = Path("data/processed/chunks.jsonl")


def load_params() -> dict:
    with open("params.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)["ingest"]


def build_chunks(
    vault_path: Path, include_dirs, exclude_dirs, max_chars, overlap_chars
):
    return
