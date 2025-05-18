"""
Реализация сервисов телеметрии и трассировки.
"""

import time
from typing import Any

import httpx
from fastapi import status
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from openverse_applaunch.objects.abc import AbstractTracerService
from openverse_applaunch.objects.models import ServiceStatus
from openverse_applaunch.objects.models.health import (
    HealthCheckResult,
    HealthyResult,
    UnhealthyResult,
    UnknownResult,
)
from openverse_applaunch.objects.types import Sentinal


class JaegerService(AbstractTracerService[HealthCheckResult]):
    """
    Сервис трассировки на основе Jaeger.

    Предоставляет интеграцию с системой распределенной трассировки Jaeger
    через протокол OpenTelemetry.
    """

    service_name = "jaeger"
    _initialized: bool = False

    async def init(self, service_name: str, endpoint: str | None = Sentinal) -> None:
        """
        Инициализирует провайдера трассировки и экспортер для Jaeger.

        Args:
            service_name: Имя сервиса для трассировки
            endpoint: URL эндпоинта Jaeger, по умолчанию http://localhost:4318/v1/traces
        """
        resource = Resource(attributes={SERVICE_NAME: service_name})
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)

        otlp_exporter = OTLPSpanExporter(
            endpoint=("http://localhost:4318/v1/traces"
                      if endpoint is Sentinal else endpoint)
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace_provider.add_span_processor(span_processor)

        console_exporter = ConsoleSpanExporter()
        trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))

        type(self)._initialized = True

    async def clean(self, *args: Any, **kwargs: Any) -> None:
        """
        Очищает ресурсы сервиса трассировки.
        """
        type(self)._initialized = False

        provider = trace.get_tracer_provider()

        shutdown_method = getattr(provider, 'shutdown', None)
        if callable(shutdown_method):
            shutdown_method()

    async def health_check(self) -> HealthCheckResult:
        """
        Проверяет доступность Jaeger API.

        Returns:
            HealthCheckResult: Результат проверки здоровья

        Raises:
            ValueError: Если сервис не инициализирован
        """
        if not self._initialized:
            raise ValueError(f"Service {self.service_name} is not initialized")

        try:
            async with httpx.AsyncClient() as client:
                start_time = time.perf_counter()
                response = await client.get("http://localhost:16686/api/health")
                response_time = (
                    time.perf_counter() - start_time
                )

                if response.status_code == status.HTTP_200_OK:
                    return HealthyResult(
                        service_name=self.service_name,
                        response_time=response_time,
                    )
                else:
                    return UnhealthyResult(
                        service_name=self.service_name,
                        status=ServiceStatus.UNHEALTHY,
                        details=response.json(),
                        response_time=response_time,
                    )

        except httpx.RequestError as exc:
            return UnknownResult(
                service_name=self.service_name,
                status=ServiceStatus.UNHEALTHY,
                message=str(exc),
            )
