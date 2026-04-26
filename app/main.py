from __future__ import annotations

"""Rotas da API."""

from pathlib import Path

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.auth import RBACPolicyEvaluator, get_policy_evaluator, require_permission
from app.observability import LocalMetrics, ObservabilityMiddleware
from app.repository import InMemoryRepository
from app.service import CotistaService


class CotistaCreateInput(BaseModel):
    """Body do POST /cotistas."""
    nome: str = Field(min_length=1)
    documento: str = Field(min_length=1)


class CotistaOutput(BaseModel):
    """Resposta padrão dos endpoints."""
    id: str
    nome: str
    documento: str


def create_app(policy_path: Path | None = None) -> FastAPI:
    """Cria a aplicação (útil para testes e para o uvicorn)."""
    app = FastAPI(title="Mini API Cadastro de Cotista")

    repository = InMemoryRepository()
    service = CotistaService(repository)
    metrics = LocalMetrics()
    evaluator = RBACPolicyEvaluator(
        policy_path or Path(__file__).resolve().parents[1] / "policies" / "rbac_policy.json"
    )

    # Middleware de logs
    app.add_middleware(ObservabilityMiddleware, metrics=metrics)

    # RBAC
    app.dependency_overrides[get_policy_evaluator] = lambda: evaluator

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check da API."""
        return {"status": "ok"}

    @app.get(
        "/cotistas/{cotista_id}",
        response_model=CotistaOutput,
        dependencies=[Depends(require_permission("cotistas", "read"))],
    )
    def get_cotista(cotista_id: str) -> CotistaOutput:
        """Consulta cotista por ID (requer `cotistas:read`)."""
        cotista = service.get_cotista(cotista_id)
        return CotistaOutput.model_validate(cotista.__dict__)

    @app.post(
        "/cotistas",
        response_model=CotistaOutput,
        status_code=201,
        dependencies=[Depends(require_permission("cotistas", "create"))],
    )
    def create_cotista(payload: CotistaCreateInput) -> CotistaOutput:
        """Cadastra cotista (requer `cotistas:create`)."""
        cotista = service.create_cotista(nome=payload.nome, documento=payload.documento)
        return CotistaOutput.model_validate(cotista.__dict__)

    return app


# Instância padrão para `uvicorn app.main:app --reload`.
app = create_app()
