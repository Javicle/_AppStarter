"""
Tracer Manager for OpenTelemetry.
"""
import asyncio
from openverse_applaunch.objects.abc.service import (
    AbstractTracerService,
    TracersDictType,
)
from openverse_applaunch.objects.exceptions import (
    TracerAlreadyExistsError,
    TracerNotFoundError,
)


class TracerManager:
    """
    Manager for OpenTelemetry tracers.
    Provides functionality to register, initialize, and manage tracing services.

    Attributes:
        tracers (TracersDictType): Dictionary of registered tracing services.
    """
    def __init__(self) -> None:
        """Initialize the tracer manager with an empty tracers dictionary."""
        self.tracers: TracersDictType = {}

    async def initialize_tracers(self) -> None:
        """
        Initialize all registered tracers asynchronously.

        Example:
            ```python
            # Initialize all registered tracers
            await tracer_manager.initialize_tracers()
            ```
        """
        await asyncio.gather(
            *(asyncio.create_task(tracer.init()) for tracer in self.tracers.values())
        )

    def add_tracer(self, service: AbstractTracerService) -> None:
        """
        Add a tracer service to the manager.

        Attributes:
            service: The tracing service instance to add.

        Raises:
            TracerAlreadyExistsError: If a tracer with the same name already exists.

        Example:
            ```python
            # Create and add a tracer service
            jaeger_tracer = JaegerTracerService(service_name="my-service")
            tracer_manager.add_tracer(jaeger_tracer)
            ```
        """
        if service.service_name in self.tracers or service in self.tracers.values():
            raise TracerAlreadyExistsError(
                f"Tracer with name '{
                    service.service_name
                }' or '{service}' already exists"
            )
        self.tracers[service.service_name] = service

    def remove_tracer(self, service_name: str) -> None:
        """
        Remove a tracer from the manager.

        Attributes:
            service_name: Name of the tracing service to remove.

        Raises:
            TracerNotFoundError: If the tracer with the given name doesn't exist.

        Example:
            ```python
            # Remove a tracer by name
            tracer_manager.remove_tracer("my-service")
            ```
        """
        if service_name not in self.tracers:
            raise TracerNotFoundError(
                f"Tracer with name '{service_name}' does not exist"
            )
        del self.tracers[service_name]

    def get_tracer(self, service_name: str) -> AbstractTracerService:
        """
        Get a tracer by name.

        Attributes:
            service_name: Name of the tracing service.

        Returns:
            AbstractTracerService: The tracing service instance.

        Raises:
            TracerNotFoundError: If the tracer with the given name doesn't exist.

        Example:
            ```python
            # Get a specific tracer
            jaeger_tracer = tracer_manager.get_tracer("jaeger-service")
            ```
        """
        if service_name not in self.tracers:
            raise TracerNotFoundError(
                f"Tracer with name '{service_name}' does not exist"
            )
        return self.tracers[service_name]
