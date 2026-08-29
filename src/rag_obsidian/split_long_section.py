from typing import List

"""

    Se encarga de dividir chunks de texto en bloques maximos de 1000 caracteres
    Primero verifica si el texto esta por debajo de la longitud maxima, si lo està
    unicamente la regresa.

    Actualiza el final de la cadena actual sumando 1000 caracteres en cada iteracion
    Verifica si el final actual tiene mas caracteres que el maximo aceptado, si es asi
    detiene el flujo y devuelve los datos.



"""


def split_long_section(
    section_text: str, max_chars: int = 1000, overlap_chars: int = 200
) -> List[str]:

    if len(section_text) <= max_chars:
        return [section_text]

    chunks: List[str] = []
    start = 0
    text_length = len(section_text)

    while start < text_length:
        end = start + max_chars

        if end >= text_length:
            chunks.append(section_text[start:].strip())  # Strip ?
            break

        # Pendiente de documentar
        breakpoint_index = section_text.rfind("\n", start + max_chars // 2, end)
        if breakpoint_index == -1:
            breakpoint_index = section_text.rfind(".", start + max_chars // 2, end)

        chunks_str = section_text[start:end].strip()
        if chunks_str:
            chunks.append(chunks_str)

        start = end - overlap_chars

    return chunks
