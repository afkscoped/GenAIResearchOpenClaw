from abc import ABC, abstractmethod
from typing import Any


class IngestionAdapter(ABC):
    source_name: str

    @abstractmethod
    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        raise NotImplementedError
