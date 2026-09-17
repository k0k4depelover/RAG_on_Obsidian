"""
Esta parte del codigo se encarga de tomar el directorio con los chunks
creados en la fase anterior del pipeline y pasarlos a travez de modelo
de embeddings creando los vectores que serán almacenados en QDrant
"""

"""
json nos sirve para leer cada linea de chunks.jsonl que tiene un objeto
JSON por cada linea.

Despues tenemos Path que nos permite manejar las rutas de archivo de forma
mas segura qeu con strings crudos basicos.

yaml se usa para leer params.yaml el cual es el archivo de configuracion en
formato YAML

Despues está BGEM3FlagModel se encarga de cargar el modelo BGE-M3 y espone
el metodo .encode() para generar vectores

"""

import json
from pathlib import Path

import pandas as pd
from FlagEmbedding import BGEM3FlagModel

from rag_obsidian.configuration.load_params import load_params

CHUNKS_PATH = Path("data/processed/chunks.jsonl")
OUTPUT_PATH = Path("data/processed/embeddings.parquet")

"""
Esta funcion se encarga de cargar los parametros del archivo de configuracion
finalmente utiliza el metodo safe_load que convierte un archivo yaml en un
diccionario anidado de python
"""


"""
Abre un archivo y recorre cada una de las lineas
posteriormente guarda esos objetos usando json.loads()
el cual se encarga de convertir el string en un diccionario de python,
acumulando cada uno de los diccionarios de python

"""


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


"""
Carga los parametros de configuracion,
carga la lista de chunks, el conjunto de archivos que se genero en el paso
anterior del pipeline.

Posteriormente se carga el modelo usando fp16 para usar la aceleracion
de GPU.
Carga el nombre del modelo en la configuracion.


Despues se utiliza una comprehension list para poder recorrer cada diccionario generado
al cargar los chunks, recordadando que la funcion nos da una lista de diccionarios, en la cual
podemos acceder a las claves.
"""


def main():
    params = load_params()
    chunks = load_chunks(CHUNKS_PATH)

    if not chunks:
        raise ValueError(
            f"No se encontraron chunks en {CHUNKS_PATH}, debe ejecutarse el ingest primero."
        )

    model = BGEM3FlagModel(params["model_name"], use_fp16=params.get("use_fp6", False))

    texts = [c["text"] for c in chunks]

    print(
        f"[embed] Generando embeddings para  {len(texts)} chunks (batch_size={params['batch_size']}) ..."
    )

    """
    Se generan los embeddings utilizando la configuracion del modelo
    cargando los textos, la configuracion del tamaño de los vectores,
    La longitud maxima, y con 3 parametros extra como return_dense lo cual
    lo configura para usar un vector denso, y los otros 2 sirven para configurar el modelo
    para que no calcula las otras representaciones que puede generar (lexica y multi-vector)
    ¿Qué devuelve model.encode(...)? Un diccionario. Como pediste return_dense=True pero los otros
    dos en False, ese diccionario va a tener (al menos) la clave "dense_vecs", y probablemente las
    claves "lexical_weights" y "colbert_vecs" en None o simplemente ausentes (dependiendo de la
    versión de la librería).
    """

    result = model.encode(
        texts,
        batch_size=params["batch_size"],
        max_length=params.get("max_length", 1024),
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )

    dense_vectors = result["dense_vecs"]

    rows = []
    for chunk, vector in zip(chunks, dense_vectors):
        rows.append(
            {
                "text": chunk["text"],
                "source_path": chunk["source_path"],
                "note_title": chunk["note_title"],
                "header_path": chunk["header_path"],
                "tags": chunk["tags"],
                "chunk_index": chunk["chunk_index"],
                "vector": vector.tolist(),
            }
        )

    df = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print(
        f"[embed] {len(df)} embeddings guardados en {OUTPUT_PATH} (dim={len(dense_vectors[0])})"
    )


if __name__ == "__main__":
    main()
