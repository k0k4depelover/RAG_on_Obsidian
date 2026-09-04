from typing import List

"""

    Se encarga de dividir chunks de texto en bloques maximos de 1000 caracteres
    Primero verifica si el texto esta por debajo de la longitud maxima, si lo està
    unicamente la regresa.

    Actualiza el final de la cadena actual sumando 1000 caracteres en cada iteracion
    Verifica si el final actual tiene mas caracteres que el maximo aceptado, si es asi
    detiene el flujo y devuelve los datos.


    Ademas, utiliza un mecanismo para escoger un breakpoint valido, definiendolo por la prioridad que definimos
    primero buscamos saltos de linea, despues buscamos puntos y en ultima instancia utilizamos comas, esto
    para no cortar el contexto de los embeddings.

    Finalmente agregamos un rango de overlaps, por lo que si un texto tiene 1001 caracteres no va dividirse
    por longitudes de 1000 y 1, si no de aproximadamente 800 y 200, dependiendo de la estructura,
    finalmente retornamos los chunks


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
        if end > text_length:
            chunks.append(section_text[start:].strip())
            break

        breakpoint_index = section_text.rfind("\n", (start + max_chars) // 2)
        if breakpoint_index == -1:
            breakpoint_index = section_text.rfind(".", (start + max_chars) // 2)
        if breakpoint_index == -1:
            breakpoint_index = section_text.rfind(",", (start + max_chars) // 2)

        if breakpoint_index != 1:
            end = breakpoint_index + 1

        chunk = section_text[start:end]

        if chunk:
            chunks.append(chunk)

        start = end - overlap_chars
    return chunks
