from __future__ import annotations

"""Regras de autorização (RBAC)."""

import json
from pathlib import Path

from fastapi import Depends, Header, HTTPException, status


class RBACPolicyEvaluator:
    """Carrega e avalia permissões no formato `recurso:acao`."""

    def __init__(self, policy_path: Path) -> None:
        """Carrega o arquivo de política."""
        policy_data = json.loads(policy_path.read_text(encoding="utf-8"))
        self._policy = policy_data.get("roles", {})

    def is_allowed(self, role: str, resource: str, action: str) -> bool:
        """Retorna True se a role contiver a permissão `<resource>:<action>`."""
        permissions = self._policy.get(role, [])
        expected_permission = f"{resource}:{action}"
        return expected_permission in permissions


def get_role_from_header(x_role: str | None = Header(default=None)) -> str:
    """Extrai a role do header `x-role`."""
    if not x_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header x-role obrigatorio.",
        )
    return x_role.lower()


def require_permission(resource: str, action: str):
    """Dependência: exige permissão em uma rota."""

    def dependency(
        role: str = Depends(get_role_from_header),
        evaluator: RBACPolicyEvaluator = Depends(get_policy_evaluator),
    ) -> None:
        """Valida permissão e lança 403 quando negar."""
        if not evaluator.is_allowed(role=role, resource=resource, action=action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado para role '{role}' em {resource}:{action}.",
            )

    return dependency


def get_policy_evaluator() -> RBACPolicyEvaluator:
    """Usado pelo FastAPI para obter o avaliador RBAC."""
    raise RuntimeError("Policy evaluator nao configurado.")
