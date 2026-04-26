"""Testes do fluxo principal da API (create + get + validação)."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    """Cria um app de teste com a mesma política RBAC do projeto."""
    app = create_app(policy_path=Path(__file__).resolve().parents[1] / "policies" / "rbac_policy.json")
    return TestClient(app)


def test_create_and_get_cotista_happy_path() -> None:
    """Admin cria; analista consulta; CNPJ retorna normalizado."""
    client = _client()

    create_resp = client.post(
        "/cotistas",
        headers={"x-role": "admin"},
        json={"nome": "Maria", "documento": "11.444.777/0001-61"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["nome"] == "Maria"
    assert created["documento"] == "11444777000161"

    get_resp = client.get(f"/cotistas/{created['id']}", headers={"x-role": "analista"})
    assert get_resp.status_code == 200
    found = get_resp.json()
    assert found["id"] == created["id"]


def test_create_cotista_with_invalid_cnpj_returns_422() -> None:
    """CNPJ inválido retorna 422."""
    client = _client()
    response = client.post(
        "/cotistas",
        headers={"x-role": "admin"},
        json={"nome": "Cliente X", "documento": "12.345.678/0001-00"},
    )
    assert response.status_code == 422
