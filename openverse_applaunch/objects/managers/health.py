import asyncio
from typing import Optional

from openverse_applaunch.objects.base import AbstractTracerService, HealthCheckResult
from openverse_applaunch.objects.exceptions import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
)


class HealthManager:
    def __init__(self) -> None:
        self.services: dict[str, AbstractTracerService] = {}
        self.health_states: dict[str, HealthCheckResult] = {}

    def register_service(self, service: AbstractTracerService) -> None:
        if service.service_name in self.services:
            raise ServiceAlreadyExistsError(f"Service {service.service_name} already registered")
        self.services[service.service_name] = service

    def unregister_service(
        self, service: Optional[AbstractTracerService] = None, service_name: str | None = None
    ) -> None:
        if service_name:
            if service_name not in self.services:
                raise ServiceNotFoundError(f"Service with name '{service_name}' does not exist")
            del self.services[service_name]

        elif service:
            if service not in self.services.values():
                raise ServiceNotFoundError(
                    f"Service with name '{service.service_name}' does not exist"
                )
            self.services.pop(service.service_name)

        else:
            raise ValueError("At least one of 'service' or 'service_name' must be provided")

    async def check_service(self, service_name: str) -> HealthCheckResult:
        service = self.services.get(service_name)
        if not service:
            raise ServiceNotFoundError(f"Service with name '{service_name}' does not exist")
        return await service.health_check()

    async def check_services(self) -> dict[str, HealthCheckResult]:
        if not self.services:
            raise ValueError("No services registered")

        health_states = await asyncio.gather(
            *(
                asyncio.create_task(self.check_service(service_name=service_name))
                for service_name in self.services.keys()
            )
        )

        if not health_states:
            raise ValueError("No services available for health check")

        for service_name, health_state in zip(self.services.keys(), health_states):
            self.health_states[service_name] = health_state

        return self.health_states
