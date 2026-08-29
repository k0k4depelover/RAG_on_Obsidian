import re
from typing import List, Tuple

"""
    Divide el texto en secciones basadas en la jerarquia
"""


# Pendiente de documentar completamente
def split_by_headers(content: str) -> List[Tuple[str, str]]:
    lines = content.splitlines()
    sections: List[Tuple[str, str]] = []

    header_stack: List[Tuple[int, int]] = []
    current_text: List[str] = []

    header_regex = re.compile(r"^(#{1,6})\s+(.+)$")

    for line in lines:
        match = header_regex.match(line)
        if match:
            if current_text:
                full_header_path = " > ".join(title for _, title in header_stack)
                section_content = "\n".join(current_text).strip()
                if section_content:
                    sections.append(full_header_path, section_content)
                current_text = []
            level = len(match.group(1))
            title = match.group(2).strip()

            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()
            header_stack.append(level, title)
        else:
            current_text.append(line)

    if current_text:
        full_header_path = " > ".join(title for _, title in header_stack)
        section_content = "\n".join(current_text).strip()
        if section_content:
            sections.append((full_header_path, section_content))

    return sections
