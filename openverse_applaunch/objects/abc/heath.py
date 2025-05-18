from typing import Any, Protocol, TypeAlias, TypeVar

from openverse_applaunch.objects.enum import ServiceStatus


class BaseHealthResultProtocol(Protocol):

    message: str
    status: ServiceStatus
    details: dict[str, Any]


class HealthyResultProtocol(BaseHealthResultProtocol):
    """Object representing information about a healthy"""

    response_time: float


class UnhealthyResultProtocol(BaseHealthResultProtocol):
    """Object representing information about an unhealthy"""

    response_time: float


class UnknownResultProtocol(BaseHealthResultProtocol):
    """Object representing information about an unknown result"""


HealthResultProtocolType: TypeAlias = (
    HealthyResultProtocol | UnhealthyResultProtocol | UnknownResultProtocol
)

THeatlhResult = TypeVar("THeatlhResult", bound="HealthResultProtocolType")
