import json
import uuid
from pathlib import Path

import pandas as pd
from configuration.load_params import load_params
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

EMBEDDINGS_PATH = Path("data/processed/embeddings.parquet")
MANIFEST_PATH = Path("data/processed/index_manifest.json")


def ensure_collection(client: QdrantClient, name: str, vector_size: int):
    existing = [c.name for c in client.get_collections().collections()]
    if name in existing:
        print(f"[index] Collection {name} ya existe")
        return
    client.create_collection(
        collection_name=name,
        vector_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    print(f"[index] Coleccion '{name}' creada (dim={vector_size}, distancia=coseno).")


def build_point(row: pd.Series) -> PointStruct:
    point_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"{row['source_path']}::{row['chunk_index']}")
    )


def main():
    params = load_params()
    df = pd.read_parquet(EMBEDDINGS_PATH)

    if df.empty:
        raise ValueError(f"No hay embeddings disponibles en {EMBEDDINGS_PATH}")

    vector_size = len(df.iloc[0]["vector"])

    client = QdrantClient(host=params["host"], port=params["port"])
    ensure_collection(client, params["collection_name"], vector_size)

    points = [build_point(row) for _, row in df.iterrows()]

    batch_size = 128

    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=params["collection_name"], points=points[i : i + batch_size]
        )

        manifest = {
            "collection_name": params["collection_name"],
            "points_upserted": len(points),
            "vector_size": vector_size,
        }

        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(
        f"[index] {len(points)} puntos subidos a la coleccion '{params['collection_name']}'."
    )


if __name__ == "__main__":
    main()
