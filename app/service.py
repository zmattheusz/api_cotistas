from __future__ import annotations

"""Regras de negócio do fluxo de cotista (inclui validação de CNPJ numérico)."""

import re
from uuid import uuid4

from fastapi import HTTPException, status

from app.repository import CotistaRecord, InMemoryRepository

_CLEANUP_PATTERN = re.compile(r"[.\-\/\s]")
_FIRST_DV_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_SECOND_DV_WEIGHTS = [6, *_FIRST_DV_WEIGHTS]


class CotistaService:
    """Orquestra o fluxo de consulta e cadastro de cotista."""

    def __init__(self, repository: InMemoryRepository) -> None:
        """Recebe o repositório (persistência)."""
        self._repository = repository

    def get_cotista(self, cotista_id: str) -> CotistaRecord:
        """Busca cotista por ID (404 se não existir)."""
        cotista = self._repository.get_cotista(cotista_id)
        if cotista is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cotista nao encontrado.",
            )
        return cotista

    def create_cotista(self, nome: str, documento: str) -> CotistaRecord:
        """Cria cotista (valida nome e CNPJ; retorna 422 em caso de erro)."""
        cleaned_name = nome.strip()
        if not cleaned_name or not documento.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Nome e documento sao obrigatorios.",
            )
        try:
            cleaned_document = _normalize_and_validate_cnpj(documento)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        record = CotistaRecord(id=str(uuid4()), nome=cleaned_name, documento=cleaned_document)
        return self._repository.create_cotista(record)


def _normalize_and_validate_cnpj(documento: str) -> str:
    """Normaliza e valida CNPJ numérico (14 dígitos + DV módulo 11)."""
    normalized = _CLEANUP_PATTERN.sub("", documento.strip())
    if len(normalized) != 14:
        raise ValueError("CNPJ deve conter 14 digitos apos remover mascara.")
    if not normalized.isdigit():
        raise ValueError("CNPJ aceita apenas numeros (formato legado). CNPJ alfanumerico e proximo passo.")
    if _all_same_digits(normalized):
        raise ValueError("CNPJ numerico invalido.")
    if not _validate_numeric_mod11(normalized):
        raise ValueError("CNPJ numerico com digitos verificadores invalidos.")
    return normalized


def _calculate_dv(values: list[int], weights: list[int]) -> int:
    """Calcula um dígito verificador (módulo 11)."""
    total = sum(value * weight for value, weight in zip(values, weights))
    remainder = total % 11
    digit = 11 - remainder
    return 0 if digit >= 10 else digit


def _validate_numeric_mod11(normalized: str) -> bool:
    """Recalcula os DVs e compara com os dois últimos dígitos."""
    base_values = [int(c) for c in normalized[:12]]
    first_dv = _calculate_dv(base_values, _FIRST_DV_WEIGHTS)
    second_dv = _calculate_dv([*base_values, first_dv], _SECOND_DV_WEIGHTS)
    return f"{first_dv}{second_dv}" == normalized[12:]


def _all_same_digits(value: str) -> bool:
    """Rejeita sequências como 000...0, 111...1, etc."""
    return all(char == value[0] for char in value)
