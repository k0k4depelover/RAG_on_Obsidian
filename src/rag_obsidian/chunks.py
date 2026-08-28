from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    text: str
    source_path: str
    note_title: str
    header_path: str
    tags: List[str] = field(default_factory=list)
    chunk_index: int = 0
