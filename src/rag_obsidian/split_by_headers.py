import re
from typing import List, Tuple

"""
    Divide el texto en secciones basadas en la jerarquia

    ENTRADA:
    # Introducción
    Texto general.

    ## Contexto
    Detalle del contexto.

    ### Antecedentes
    Más detalle aún. uv creo que era, o no

    ## Objetivos
    Texto de objetivos.


    SALIDA:

    [
    ("Introducción", "Texto general."),
    ("Introducción > Contexto", "Detalle del contexto."),
    ("Introducción > Contexto > Antecedentes", "Más detalle aún."),
    ("Introducción > Objetivos", "Texto de objetivos."),
    ]

"""


def split_by_headers(content: str) -> List[Tuple[str, str]]:
    lines: str = content.splitlines()

    # Representa una lista enumerada con las secciones segun la jerarquia
    # [(1, "Intro"), (2, "Sub"), (3, "Detalle")]

    sections: List[Tuple[str, str]] = []
    header_stack: List[Tuple[int, str]] = []

    # Lista de líneas de texto "normal"
    # que se van acumulando hasta que aparece el siguiente encabezado
    current_text: List[str] = []
    header_regex = re.compile(r"(^#{1,6})\s+(.+)")

    for line in lines:
        match = header_regex.match(line)
        if match:
            if current_text:
                full_header_path = " > ".join(title for _, title in header_stack)
                section_content = "\n".join(current_text).strip()
                if section_content:
                    sections.append((full_header_path, section_content))
                current_text = []
            level = len(match.group(1))
            title = match.group(2).strip()

            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()

            header_stack.append((level, title))
        else:
            current_text.append(line)

    if current_text:
        full_header_path = " > ".join(title for _, title in header_stack)
        section_content = "\n".join(current_text).strip()
        if section_content:
            sections.append((full_header_path, section_content))

    return sections
