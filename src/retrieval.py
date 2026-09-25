import gc
import sys

import requests
import torch
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient

from rag_obsidian.configuration.load_params import load_params


def embed_question(question: str, model_name: str, use_fp16: bool) -> list[float]:
    """
    Vectoriza la pregunta con el modelo BGE-M3
    Se encarga de quitar el mmodelo de la GPU al terminar para que
    pueda usar la VRAM Ollama
    """
    print(f"[Retrieval] Cargando {model_name}. USE_FP16: {use_fp16}")

    model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

    result = model.encode(
        [question], return_dense=True, return_sparse=False, return_colbert_vecs=False
    )

    vector = result["dense_vecs"][0].tolist()

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return vector


def search_qdrant(
    client: QdrantClient, collection_name: str, query_vector: list[float], top_k: int
):
    """
    Busqueda semantica: le pide a Qdrant los top_k puntos mas
    similares (coseno) al vector de la pregunta.
    """

    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
    ).points
    return results


def build_context(results) -> str:
    """
    Busqueda semantica: le pide a Qdrant los top_k puntos mas
    similares (coseno) al vector de la pregunta.
    """
    blocks = []
    for i, point in enumerate(results, start=1):
        payload = point.payload
        blocks.append(
            f"[Fragmento {i} | fuente: {payload['source_path']} | seccion: {payload['header_path']}]\n"
            f"{payload['text']}"
        )
    return "\n\n".join(blocks)


def build_prompt(question: str, context: str) -> str:
    """
    El 'Argumented Prompt' de tu diagrama: combina el contexto
    recuperado con la pregunta original, con instrucciones explicitas
    de apegarse solo al contexto dado.
    """
    return f"""Eres un asistente que responde preguntas basandote UNICAMENTE en el contexto proporcionado.
Si la respuesta no esta en el contexto, di explicitamente que no encontraste esa informacion en las notas.
No inventes informacion que no este en el contexto.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""


def ask_llm(prompt: str, model_name: str, host: str, port: int, temperature: float):
    response = requests.post(
        f"http://{host}:{port}/api/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
    )
    response.raise_for_status()
    return response.json()["response"]


def main():
    if (len(sys.argv)) < 2:
        print('Uso: python test_retrieval.py "tu pregunta aqui"')
        sys.exit(1)

    question = sys.argv[1]

    embed_params = load_params("embed")
    qdrant_params = load_params("qdrant")
    retrieval_params = load_params("retrieval")
    llm_params = load_params("llm")

    query_vector = embed_question(
        question,
        model_name=embed_params["model_name"],
        use_fp16=embed_params.get("use_fp16", False),
    )

    client = QdrantClient(host=qdrant_params["host"], port=qdrant_params["port"])
    results = search_qdrant(
        client,
        collection_name=qdrant_params["collection_name"],
        query_vector=query_vector,
        top_k=retrieval_params["top_k"],
    )

    if not results:
        print("[retrieval] No se encontraron chunks relevantes en Qdrant.")
        sys.exit(0)

    print(f"[retrieval] {len(results)} chunks recuperados:")
    for r in results:
        print(
            f"  - score={r.score:.4f} | {r.payload['source_path']} > {r.payload['header_path']}"
        )

    context = build_context(results)
    prompt = build_prompt(question, context)
    print(f"\n[retrieval] Generando respuesta con {llm_params['model_name']} ...")
    answer = ask_llm(
        prompt,
        model_name=llm_params["model_name"],
        host=llm_params["host"],
        port=llm_params["port"],
        temperature=llm_params.get("temperature", 0.2),
    )

    print("\n" + "=" * 60)
    print("RESPUESTA:")
    print("=" * 60)
    print(answer)


if __name__ == "__main__":
    main()
