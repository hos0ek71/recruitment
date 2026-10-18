from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawItem:
    source_posting_id: str
    payload: dict[str, Any]
