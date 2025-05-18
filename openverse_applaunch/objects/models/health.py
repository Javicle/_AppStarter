"""
Модели для проверки здоровья сервисов.
Module for checking health of services
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, MutableMapping, TypeAlias

from openverse_applaunch.objects.abc.heath import (
    HealthyResultProtocol,
    UnhealthyResultProtocol,
    UnknownResultProtocol,
)
from openverse_applaunch.objects.enum import ServiceStatus


@dataclass(kw_only=True)
class _BaseHealthResult:
    """Base class for health status result."""

    service_name: str
    last_check_time: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class HealthyResult(_BaseHealthResult, HealthyResultProtocol):
    response_time: float
    message: str = "Service is healthy"
    status: ServiceStatus = ServiceStatus.HEALTHY
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class UnhealthyResult(_BaseHealthResult, UnhealthyResultProtocol):
    response_time: float
    message: str = "Service is unhealthy"
    status: ServiceStatus = ServiceStatus.UNHEALTHY
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class UnknownResult(_BaseHealthResult, UnknownResultProtocol):
    message: str = "Service health is unknown"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    details: dict[str, Any] = field(default_factory=dict)


HealthCheckResult: TypeAlias = HealthyResult | UnhealthyResult | UnknownResult

HealthCheckDict: TypeAlias = MutableMapping[str, HealthCheckResult]
