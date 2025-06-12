"""
Metrics Manager for application metrics with logging.
"""
import asyncio
from typing import Any

from rich.console import Console
from tools_openverse import setup_logger

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
        logger (logging.Logger): Logger instance for this manager.
    """

    def __init__(self, console: Console) -> None:
        """
        Initialize the metrics manager.

        Attributes:
            console: Console for output information.
        """
        self.console = console
        self.services: dict[str, AbstractMetricsService] = {}
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info("Metrics manager initialized")

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
        self.logger.debug(
            f"Attempting to register metrics service: {service.service_name}"
        )

        if service.service_name in self.services:
            self.logger.error(
                f"Metrics service registration failed: service '{
                    service.service_name
                }' already exists"
            )
            raise ServiceAlreadyExistsError(
                f"Service {service.service_name} already exists"
            )

        self.services[service.service_name] = service
        self.logger.info(
            f"Successfully registered metrics service: {service.service_name}"
        )

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
        self.logger.debug(f"Retrieving metrics service: {service_name}")

        if service_name not in self.services:
            self.logger.error(
                f"Metrics service retrieval failed: '{service_name}' not found"
            )
            raise ServiceNotFoundError(f"Service {service_name} does not exist")

        service = self.services[service_name]
        self.logger.debug(f"Successfully retrieved metrics service: {service_name}")
        return service

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
        self.logger.debug(f"Attempting to remove metrics service: {service_name}")

        if service_name not in self.services:
            self.logger.error(
                f"Metrics service removal failed: '{service_name}' not found"
            )
            raise ServiceNotFoundError(f"Service {service_name} does not exist")

        self.services.pop(service_name)
        self.logger.info(f"Successfully removed metrics service: {service_name}")

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
        self.logger.debug(
            f"Starting initialization of all metrics services (count: {
                len(self.services)
            })"
        )

        if not self.services:
            self.logger.error(
                "Metrics services initialization failed: no services registered"
            )
            raise ServiceNotFoundError("No metrics services registered")

        try:
            await asyncio.gather(
                *(
                    asyncio.create_task(service.init(*args, **kwargs))
                    for service in self.services.values()
                )
            )

            self.logger.info(
                f"Successfully initialized {len(self.services)} metrics services"
            )

        except Exception as exc:
            self.logger.error(f"Metrics services initialization failed: {exc}")
            raise
