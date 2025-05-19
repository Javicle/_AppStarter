"""
Metrics Manager for application metrics.
"""
import asyncio
from typing import Any
from rich.console import Console
from openverse_applaunch.objects.abc.service import AbstractMetricsService
from openverse_applaunch.objects.exceptions import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
)


class MetricsManager:
    """
    Manager for application metrics.
    Provides functionality to register, initialize,
    and manage metrics collection services.

    Attributes:
        console (Console): Console for output information.
        services (dict): Dictionary of registered metrics services.
    """

    def __init__(self, console: Console) -> None:
        """
        Initialize the metrics manager.

        Attributes:
            console: Console for output information.
        """
        self.console = console
        self.services: dict[str, AbstractMetricsService] = {}

    def register_service(self, service: AbstractMetricsService) -> None:
        """
        Register a metrics service.

        Attributes:
            service: Metrics service to register.

        Raises:
            ServiceAlreadyExistsError: If a service with the same name already exists.

        Example:
            ```python
            # Create and register a Prometheus metrics service
            prometheus = PrometheusMetricsService(service_name="prometheus")
            metrics_manager.register_service(prometheus)
            ```
        """
        if service.service_name in self.services:
            raise ServiceAlreadyExistsError(
                f"Service {service.service_name} already exists"
            )
        self.services[service.service_name] = service

    def get_service(self, service_name: str) -> AbstractMetricsService:
        """
        Get a metrics service by name.

        Attributes:
            service_name: Name of the metrics service.

        Returns:
            AbstractMetricsService: The metrics service instance.

        Raises:
            ServiceNotFoundError: If the service with the given name doesn't exist.

        Example:
            ```python
            # Get a specific metrics service
            prometheus = metrics_manager.get_service("prometheus")
            ```
        """
        if service_name not in self.services:
            raise ServiceNotFoundError(f"Service {service_name} does not exist")
        return self.services[service_name]

    def remove_service(self, service_name: str) -> None:
        """
        Remove a metrics service.

        Attributes:
            service_name: Name of the metrics service to remove.

        Raises:
            ServiceNotFoundError: If the service with the given name doesn't exist.

        Example:
            ```python
            # Remove a metrics service
            metrics_manager.remove_service("prometheus")
            ```
        """
        if service_name not in self.services:
            raise ServiceNotFoundError(f"Service {service_name} does not exist")
        del self.services[service_name]

    async def initialize_services(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize all registered metrics services.

        Attributes:
            *args: Positional arguments for initialization.
            **kwargs: Keyword arguments for initialization.

        Raises:
            ServiceNotFoundError: If no metrics services are registered.
            
        Example:
            ```python
            # Initialize all registered metrics services
            await metrics_manager.initialize_services(endpoint="/metrics")
            ```
        """
        if not self.services:
            raise ServiceNotFoundError("No metrics services registered")

        await asyncio.gather(
            *(
                asyncio.create_task(service.init(*args, **kwargs))
                for service in self.services.values()
            )
        )