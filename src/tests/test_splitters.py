import pytest

from rag_obsidian.split_by_headers import split_by_headers
from rag_obsidian.split_long_section import split_long_section


def unit_test_split_by_headers_single_header():
    """
    Test de caso base, titulo y texto.
    """

    content = "# Titulo\nTexto de la seccion."

    assert split_by_headers(content) == [("Titulo", "Texto de la seccion.")]


def test_split_by_headers_nested_hierarchy():
    """
    Verifica la construccion del header_path jerarquico (' > ')
    usando multiples niveles de anidacion (#, ##, ###),
    y al volver a un nivel superior (## Objetivos despues de
    ### Antecedentes) la pila se actualiza correctamente, sin
    arrastrar el nivel 3 que ya no aplica.
    """
    content = (
        "# Introduccion\n"
        "Texto general.\n"
        "\n"
        "## Contexto\n"
        "Detalle del contexto.\n"
        "\n"
        "### Antecedentes\n"
        "Mas detalle aun.\n"
        "\n"
        "## Objetivos\n"
        "Texto de objetivos.\n"
    )

    result = split_by_headers(content)

    assert result == [
        ("Introduccion", "Texto general."),
        ("Introduccion > Contexto", "Detalle del contexto."),
        ("Introduccion > Contexto > Antecedentes", "Mas detalle aun."),
        ("Introduccion > Objetivos", "Texto de objetivos."),
    ]


def test_split_by_headers_sibling_replaces_previous_at_same_level():
    """
    Verifica especificamente la logica del while de la pila:
    un nuevo encabezado del MISMO nivel debe reemplazar al anterior
    (no acumularse como hermano dentro del header_path).
    """
    content = "## Seccion A\nTexto A.\n\n## Seccion B\nTexto B.\n"

    result = split_by_headers(content)

    assert result == [
        ("Seccion A", "Texto A."),
        ("Seccion B", "Texto B."),
    ]


def test_split_by_headers_no_headers_returns_empty_path():
    """
    Si el documento no tiene ningun encabezado, header_stack nunca
    recibe elementos, por lo que header_path queda como cadena vacia
    ('' al hacer join de una lista vacia). Todo el texto se agrupa
    en una unica seccion.
    """
    content = "Solo texto plano.\nSin encabezados."

    result = split_by_headers(content)

    assert result == [("", "Solo texto plano.\nSin encabezados.")]


def test_split_by_headers_skips_empty_sections_between_headers():
    """
    Si dos encabezados aparecen consecutivos sin texto entre ellos,
    no debe generarse una seccion vacia para el primero (el 'if
    section_content:' debe filtrarla). Solo debe existir la seccion
    final que si tiene contenido.
    """
    content = "# A\n## B\nTexto B."

    result = split_by_headers(content)

    # No debe existir ninguna tupla con section_content == ""
    assert all(section_content for _, section_content in result)
    assert result == [("A > B", "Texto B.")]


def test_split_by_headers_strips_surrounding_whitespace():
    """
    Verifica que el contenido de cada seccion se entregue sin lineas
    en blanco sobrantes al inicio/final (efecto del .strip() aplicado
    a section_content).
    """
    content = "# Titulo\n\n\nTexto con espacios alrededor.\n\n\n"

    result = split_by_headers(content)

    assert result == [("Titulo", "Texto con espacios alrededor.")]


def test_split_by_headers_returns_list_of_tuples():
    """
    Chequeo de forma/tipo: cada elemento debe ser una tupla de 2
    strings (header_path, section_content). Este test hubiera
    fallado con el bug original de 'sections.append(a, b)' porque
    ni siquiera se habria llegado a construir la lista.
    """
    content = "# Titulo\nTexto."

    result = split_by_headers(content)

    assert isinstance(result, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
    assert all(isinstance(h, str) and isinstance(t, str) for h, t in result)


def test_split_long_section_returns_single_chunk_when_short():
    """
    Caso trivial: si el texto ya cabe en max_chars, se retorna
    tal cual, sin pasar por la ventana deslizante.
    """
    text = "Texto corto que no necesita dividirse."

    result = split_long_section(text, max_chars=1000, overlap_chars=200)

    assert result == [text]


def test_split_long_section_mechanical_cut_when_no_breakpoint_found():
    """
    Caso sin puntos de corte 'naturales': un texto de puros
    caracteres repetidos, sin '\\n' ni '.' en ninguna zona de
    busqueda. El corte debe caer exactamente en el limite mecanico
    (start + max_chars), tal como calculamos a mano:

    max_chars=20, overlap=5, texto de 45 caracteres 'a':
      iter 1: start=0,  end=20            -> chunk de 20 chars
      iter 2: start=15, end=35            -> chunk de 20 chars
      iter 3: start=30, end=50>=45 (fin)  -> chunk de 15 chars
    """
    text = "a" * 45

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert [len(c) for c in result] == [20, 20, 15]
    # Todos los caracteres deben ser 'a' (no se perdio ni se inserto nada raro)
    assert all(set(chunk) == {"a"} for chunk in result)


def test_split_long_section_uses_newline_as_intelligent_breakpoint():
    """
    Coloca un '\\n' dentro de la zona de busqueda de la primera
    ventana (entre start + max_chars//2 y end) y verifica que el
    corte ocurra justo despues de ese salto de linea, NO en el
    limite mecanico de 20 caracteres.

    texto: 12 'a' + '\\n' + 32 'a'  (el '\\n' cae en el indice 12,
    dentro de la zona de busqueda [10, 20) de la primera iteracion).

    Si el bug NO estuviera corregido, el primer chunk mediria 20
    caracteres exactos. Con el fix, debe medir 12 (el '\\n' final
    se recorta con .strip()).
    """
    text = "a" * 12 + "\n" + "a" * 32  # longitud total: 45

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert result[0] == "a" * 12
    assert len(result[0]) < 20  # confirma que NO uso el corte mecanico


def test_split_long_section_falls_back_to_period_when_no_newline():
    """
    Si no hay '\\n' en la zona de busqueda pero SI hay un '.', debe
    usar el punto como corte inteligente (segundo intento del if).

    texto: 14 'a' + '.' + 30 'a' (el '.' cae en el indice 14, dentro
    de la zona de busqueda [10, 20) de la primera iteracion, y no
    hay ningun '\\n' en todo el texto).
    """
    text = "a" * 14 + "." + "a" * 30  # longitud total: 45

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert result[0] == "a" * 14 + "."
    assert len(result[0]) < 20


def test_split_long_sections_falls_back_to_period_when_no_newline_or_dot():
    """
    Si no hay '\\n' en la zona de busqueda pero SI hay un '.', debe
    usar el punto como corte inteligente (segundo intento del if).
    Si no, en ultima instancia busca por comas.

    texto: 14 'a' + ',' + 30 'a' (el ',' cae en el indice 14, dentro
    de la zona de busqueda [10, 20) de la primera iteracion, y no
    hay ningun '\\n' en todo el texto).
    """
    text = "a" * 14 + "," + "a" * 20
    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert result == "a" * 14 + ","
    assert len(result[0]) < 20


def test_split_long_section_prefers_newline_over_period():
    """
    Si en la zona de busqueda existen AMBOS: un '.' y un '\\n', debe
    priorizar el '\\n' (el codigo solo cae al plan B del '.' cuando
    breakpoint_index == -1, es decir, cuando no encontro '\\n').

    texto: 10 'a' + '.' + 3 'a' + '\\n' + 30 'a'
    El '.' esta en indice 10, el '\\n' esta en indice 14. Ambos caen
    dentro de la zona [10, 20). Debe cortar en el '\\n' (indice 14),
    no en el '.' (indice 10).
    """
    text = "a" * 10 + "." + "a" * 3 + "\n" + "a" * 30  # longitud total: 45

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert result[0] == "a" * 10 + "." + "a" * 3
    assert "\n" not in result[0]  # el \n se corto y se stripeo, no quedo en el chunk


def test_split_long_section_overlap_between_consecutive_chunks():
    """
    Verifica que exista solapamiento real de 'overlap_chars'
    caracteres entre chunks consecutivos. Se usa un texto de digitos
    repetidos (no todos iguales, aunque ciclicos) para poder comparar
    los bordes de cada chunk contra el texto original, en vez de
    valores fijos a mano.

    Con max_chars=20 y overlap=5 sobre un texto de 50 caracteres:
      iter 1: start=0,  end=20
      iter 2: start=15, end=35
      iter 3: start=30, end=50 (fin)

    El final de chunk[0] (ultimos 5 chars) debe coincidir con el
    inicio de chunk[1] (primeros 5 chars), y lo mismo entre
    chunk[1] y chunk[2].
    """
    text = "0123456789" * 5  # longitud total: 50, sin '\n' ni '.'

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert len(result) == 3
    assert result[0][-5:] == result[1][:5]
    assert result[1][-5:] == result[2][:5]


def test_split_long_section_last_chunk_captures_remaining_text():
    """
    Verifica que el ultimo chunk contenga exactamente lo que sobra
    del texto original (sin perder ni repetir caracteres de mas al
    final), usando el mismo texto de digitos del test anterior.
    """
    text = "0123456789" * 5  # longitud total: 50

    result = split_long_section(text, max_chars=20, overlap_chars=5)

    assert result[-1] == text[30:]


def test_split_long_section_all_chunks_within_max_chars():
    """
    Invariante general: ningun chunk debe superar max_chars, sin
    importar si el corte fue mecanico o inteligente (el breakpoint
    siempre se busca ANTES de 'end', nunca despues).
    """
    text = "Lorem ipsum dolor sit amet. " * 50  # texto largo con puntos

    result = split_long_section(text, max_chars=100, overlap_chars=20)

    assert all(len(chunk) <= 100 for chunk in result)


def test_split_long_section_no_empty_chunks():
    """
    Ningun chunk devuelto debe ser una cadena vacia (protegido por
    los 'if chunks_str:' / el break temprano cuando end >= text_length).
    """
    text = "b" * 237

    result = split_long_section(text, max_chars=50, overlap_chars=10)

    assert all(chunk != "" for chunk in result)
