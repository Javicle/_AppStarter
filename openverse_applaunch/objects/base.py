import abc
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Self

import httpx
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    READY = "✅ Ready"
    ERROR = "❌ Error"
    WARNING = "⚠️ Warning"
    STARTING = "🔄 Starting"


@dataclass
class HealthCheckResult:
    status: ServiceStatus
    details: dict[str, Any] | None = None
    message: str | None = None
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None


@dataclass
class ServiceConfig:
    service_name: str
    host: str
    port: int
    version: str
    workers: int
    debug_mode: bool
    environment: str

    @classmethod
    def from_dict(cls, some_dict: dict[str, str]) -> Self:
        return cls(
            service_name=some_dict["service_name"],
            host=some_dict["host"],
            port=int(some_dict["port"]),
            version=some_dict["version"],
            workers=int(some_dict["workers"]),
            debug_mode=bool(some_dict["debug_mode"]),
            environment=some_dict["environment"],
        )

    def to_dict(self) -> dict[str, str | int | bool]:
        return {
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "version": self.version,
            "workers": self.workers,
            "debug_mode": self.debug_mode,
            "environment": self.environment,
        }


class AbstractTracerService(abc.ABC):
    service_name: str = "base_service"
    _initialized: bool = False

    @abc.abstractmethod
    async def init(self, *args: Any, **kwargs: Any) -> None: ...

    @abc.abstractmethod
    async def clean(self, *args: Any, **kwargs: Any) -> None: ...

    @abc.abstractmethod
    async def health_check(self, *args: Any, **kwargs: Any) -> HealthCheckResult: ...


@dataclass
class ServiceStatusResponse:
    service_name: str
    success: bool
    message: str

    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None


class ServiceCheck(abc.ABC):
    def __init__(self, service_name: str, **kwargs: Any):
        self.service_name = service_name
        self.kwargs = kwargs

    @abc.abstractmethod
    async def check(self) -> ServiceStatusResponse: ...


class JaegerService(AbstractTracerService):
    service_name = "jaeger"
    _initialized: bool = False

    async def init(self, service_name: str, endpoint: str | None = None) -> None:
        resource = Resource(attributes={SERVICE_NAME: service_name})
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)

        otlp_exporter = OTLPSpanExporter(endpoint=endpoint or "http://localhost:4318/v1/traces")
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace_provider.add_span_processor(span_processor)

        console_exporter = ConsoleSpanExporter()
        trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    async def health_check(self) -> HealthCheckResult:
        if not self._initialized:
            raise ValueError(f"Service {self.service_name} is not initialized")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:16686/api/health")
                return (
                    HealthCheckResult(ServiceStatus.HEALTHY)
                    if response.status_code == 200
                    else HealthCheckResult(ServiceStatus.UNHEALTHY, message=response.json())
                )

        except httpx.RequestError as exc:
            return HealthCheckResult(status=ServiceStatus.UNHEALTHY, message=str(exc))
