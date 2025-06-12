"""
Health Manager for service health monitoring with logging.
"""

import asyncio
from typing import MutableMapping

from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import IHealthManager
from openverse_applaunch.objects.abc.service import AbstractTracerService
from openverse_applaunch.objects.exceptions import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
)
from openverse_applaunch.objects.models.health import HealthCheckResult, HealthyResult
from openverse_applaunch.objects.types import Sentinal


class HealthManager(
    IHealthManager[AbstractTracerService[HealthCheckResult], HealthCheckResult]
):
    """
    Manager for service health monitoring.
    Tracks service states and provides methods for checking their health status.

    Attributes:
        services (dict): Dictionary of registered services for health checks.
        health_states (dict): Dictionary containing the latest health check results.
        logger (logging.Logger): Logger instance for this manager.
    """

    def __init__(self) -> None:
        """Initialize the health manager with empty services
        and health states dictionaries."""
        self.services: dict[str, AbstractTracerService[HealthCheckResult]] = {}
        self.health_states: dict[str, HealthCheckResult] = {}
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info("Health manager initialized")

    def register_service(
        self, service: AbstractTracerService[HealthCheckResult]
    ) -> None:
        """
        Register a service for health checks.

        Attributes:
            service: Service to register for health monitoring.

        Raises:
            ServiceAlreadyExistsError: If a service with
            the same name is already registered.

        Example:
            ```python
            # Create and register a database service for health monitoring
            db_service = DatabaseService(service_name="postgres")
            health_manager.register_service(db_service)
            ```
        """
        self.logger.debug(f"Attempting to register service: {service.service_name}")

        if service.service_name in self.services:
            self.logger.error(
                f"Service registration failed: service '{
                    service.service_name
                }' already exists"
            )
            raise ServiceAlreadyExistsError(
                f"Service with '{service.service_name}' name already registered"
            )

        self.services[service.service_name] = service
        self.logger.info(f"Successfully registered service: {service.service_name}")

    def unregister_service(
        self, service: AbstractTracerService[HealthCheckResult]
    ) -> None:
        """
        Remove a service from the health manager.

        Attributes:
            service: Service to remove from health monitoring.

        Raises:
            ServiceNotFoundError: If the service is not found.
            ValueError: If neither service nor service_name is provided.

        Example:
            ```python
            # Unregister a service by instance
            health_manager.unregister_service(db_service)
            ```
        """
        self.logger.debug(f"Attempting to unregister service: {service.service_name}")

        if service is Sentinal:
            self.logger.error("Unregister service failed: no service provided")
            raise ValueError(
                "At least one of 'service' or 'service_name' must be provided"
            )
        else:
            if service in self.services.values():
                self.services.pop(service.service_name)
                self.logger.info(
                    f"Successfully unregistered service: {service.service_name}"
                )
            else:
                self.logger.error(
                    f"Unregister service failed: service '{
                        service.service_name
                    }' not found"
                )
                raise ServiceNotFoundError(
                    f"Service with name '{service.service_name}' does not exist"
                )

    async def check_service(self, service_name: str) -> HealthCheckResult:
        """
        Check the health of a specific service.

        Attributes:
            service_name: Name of the service to check.

        Returns:
            HealthCheckResult: Result of the health check.

        Raises:
            ServiceNotFoundError: If the service with the given name doesn't exist.

        Example:
            ```python
            # Check the health of a specific service
            db_health = await health_manager.check_service("postgres")
            if db_health.is_healthy:
                print("Database is healthy")
            ```
        """
        self.logger.debug(f"Starting health check for service: {service_name}")

        service = self.services.get(service_name)
        if not service:
            self.logger.error(
                f"Health check failed: service '{service_name}' not found"
            )
            raise ServiceNotFoundError(
                f"Service with name '{service_name}' does not exist"
            )

        try:
            health_result = await service.health_check()
            self.logger.info(
                f"Health check completed for '{service_name}': "
                f"{'healthy' if health_result is HealthyResult else 'unhealthy'}"
            )
            return health_result
        except Exception as exc:
            self.logger.error(f"Health check failed for '{service_name}': {exc}")
            raise

    async def check_services(self) -> MutableMapping[str, HealthCheckResult]:
        """
        Check the health of all registered services.

        Returns:
            MutableMapping[str, HealthCheckResult]: Dictionary with
            health check results, where the key is the service name.

        Raises:
            ServiceNotFoundError: If no services are registered.
            ValueError: If no services are available for health check.

        Example:
            ```python
            # Check all services and get their health status
            health_results = await health_manager.check_services()

            # Print status of all services
            for service_name, result in health_results.items():
                print(f"{service_name}: {
                    'Healthy' if result.is_healthy else 'Unhealthy'
                }")
            ```
        """
        self.logger.debug(
            f"Starting health check for all services (count: {len(self.services)})"
        )

        if not self.services:
            self.logger.error("Health check failed: no services registered")
            raise ServiceNotFoundError("No services registered")

        try:
            health_states = await asyncio.gather(
                *(
                    asyncio.create_task(self.check_service(service_name=service_name))
                    for service_name in self.services.keys()
                )
            )

            if not health_states:
                self.logger.error("Health check failed: no health states returned")
                raise ValueError("No services available for health check")

            health_dict: dict[str, HealthCheckResult] = {
                service_name: health_state
                for service_name, health_state in zip(
                    self.services.keys(), health_states
                )
            }

            self.health_states.update(health_dict)

            # Log summary
            healthy_count = sum(
                1 for result_count in health_dict.values()
                if result_count is HealthyResult
            )
            total_count = len(health_dict)
            self.logger.info(
                f"Health check summary: {healthy_count}/{total_count} services healthy"
            )

            return self.health_states

        except Exception as exc:
            self.logger.error(f"Bulk health check failed: {exc}")
            raise

    def get_service(
        self, service_name: str
    ) -> AbstractTracerService[HealthCheckResult]:
        """
        Get a service by name.

        Attributes:
            service_name: Name of the service to retrieve.

        Returns:
            AbstractTracerService[HealthCheckResult]: The service instance.

        Raises:
            KeyError: If the service with the given name doesn't exist.

        Example:
            ```python
            # Get a registered service
            db_service = health_manager.get_service("postgres")
            ```
        """
        self.logger.debug(f"Retrieving service: {service_name}")

        try:
            service = self.services[service_name]
            self.logger.debug(f"Successfully retrieved service: {service_name}")
            return service
        except KeyError:
            self.logger.error(f"Service retrieval failed: '{service_name}' not found")
            raise
