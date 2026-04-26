from __future__ import annotations

"""Logs por requisição."""

import json
import logging
from collections import defaultdict
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("cotista_api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class LocalMetrics:
    """Contadores simples em memória."""

    def __init__(self) -> None:
        self.request_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.latency_sum_ms = defaultdict(float)

    def add_request(self, path: str, latency_ms: float, is_error: bool) -> None:
        """Acumula contadores por path."""
        self.request_count[path] += 1
        self.latency_sum_ms[path] += latency_ms
        if is_error:
            self.error_count[path] += 1

    def snapshot(self) -> dict[str, dict[str, float]]:
        """Retorna métricas agregadas."""
        data: dict[str, dict[str, float]] = {}
        for path, count in self.request_count.items():
            errors = self.error_count[path]
            avg_latency = self.latency_sum_ms[path] / count if count else 0.0
            data[path] = {
                "requests": float(count),
                "errors": float(errors),
                "avg_latency_ms": round(avg_latency, 2),
            }
        return data


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Loga cada requisição em JSON e mede latência."""

    def __init__(self, app, metrics: LocalMetrics):
        super().__init__(app)
        self._metrics = metrics

    async def dispatch(self, request: Request, call_next) -> Response:
        """Intercepta request/response e registra log + métricas."""
        started = perf_counter()
        response: Response | None = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = (perf_counter() - started) * 1000
            is_error = status_code >= 400
            self._metrics.add_request(request.url.path, elapsed_ms, is_error)
            logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "latency_ms": round(elapsed_ms, 2),
                        "is_error": is_error,
                    }
                )
            )
