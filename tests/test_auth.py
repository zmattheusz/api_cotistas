"""Testes do RBAC (401 sem role, 403 sem permissão)."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_requires_role_header() -> None:
    """Sem `x-role`, endpoints protegidos retornam 401."""
    app = create_app(policy_path=Path(__file__).resolve().parents[1] / "policies" / "rbac_policy.json")
    client = TestClient(app)

    response = client.get("/cotistas/123")

    assert response.status_code == 401
    assert "x-role" in response.json()["detail"]


def test_denies_role_without_permission() -> None:
    """Role sem permissão para `cotistas:create` retorna 403."""
    app = create_app(policy_path=Path(__file__).resolve().parents[1] / "policies" / "rbac_policy.json")
    client = TestClient(app)

    response = client.post("/cotistas", headers={"x-role": "viewer"}, json={"nome": "Joao", "documento": "123"})

    assert response.status_code == 403
