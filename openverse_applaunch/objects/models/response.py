from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias

from openverse_applaunch.objects.abc.service import (
    FailedServiceProtocol,
    OtherServiceProtocol,
    SuccessfulServiceProtocol,
)


@dataclass(kw_only=True)
class _BaseServiceStatusResponse:
    """Base class for response status of external service"""

    service_name: str
    last_check_time: datetime = field(default_factory=datetime.now)


@dataclass(kw_only=True)
class SuccessfulServiceResponse(_BaseServiceStatusResponse, SuccessfulServiceProtocol):
    """Successful status response"""

    response_time: float
    message: str = "Successful service status"


@dataclass(kw_only=True)
class FailedServiceResponse(_BaseServiceStatusResponse, FailedServiceProtocol):
    """Failed status response"""

    response_time: float
    message: str = ""

    def __post_init__(self) -> None:
        """Generate message if not provided"""
        if self.message == "":
            self.message = f"Failed to get service status for {self.service_name}"


@dataclass(kw_only=True)
class OtherServiceResponse(_BaseServiceStatusResponse, OtherServiceProtocol):
    """Other status response"""

    response_time: float
    message: str = ""

    def __post_init__(self) -> None:
        """Generate message if not provided"""
        if self.message == "":
            self.message = f"Other service status for {self.service_name}"


ServiceStatusResponse: TypeAlias = (
    SuccessfulServiceResponse | FailedServiceResponse | OtherServiceResponse
)
