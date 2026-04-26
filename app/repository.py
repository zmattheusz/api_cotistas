from __future__ import annotations

"""Repositório em memória (simulação de banco)."""

from dataclasses import dataclass
from threading import Lock


@dataclass
class CotistaRecord:
    """Modelo persistido pelo repositório."""
    id: str
    nome: str
    documento: str


class InMemoryRepository:
    """CRUD mínimo em memória (dados se perdem ao reiniciar)."""

    def __init__(self) -> None:
        self._records: dict[str, CotistaRecord] = {}
        self._lock = Lock()

    def get_cotista(self, cotista_id: str) -> CotistaRecord | None:
        """Retorna o registro ou None."""
        return self._records.get(cotista_id)

    def create_cotista(self, record: CotistaRecord) -> CotistaRecord:
        """Insere/atualiza o registro pelo id."""
        with self._lock:
            self._records[record.id] = record
        return record
