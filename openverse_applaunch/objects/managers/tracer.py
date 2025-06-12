"""
Tracer Manager for OpenTelemetry with logging.
"""
import asyncio

from tools_openverse import setup_logger

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
        logger (logging.Logger): Logger instance for this manager.
    """
    def __init__(self) -> None:
        """Initialize the tracer manager with an empty tracers dictionary."""
        self.tracers: TracersDictType = {}
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info("Tracer manager initialized")

    async def initialize_tracers(self) -> None:
        """
        Initialize all registered tracers asynchronously.

        Example:
            ```python
            # Initialize all registered tracers
            await tracer_manager.initialize_tracers()
            ```
        """
        self.logger.debug(
            f"Starting initialization of all tracers (count: {len(self.tracers)})"
        )

        if not self.tracers:
            self.logger.warning("No tracers registered for initialization")
            return

        try:
            await asyncio.gather(
                *(
                    asyncio.create_task(tracer.init())
                    for tracer in self.tracers.values()
                )
            )

            self.logger.info(f"Successfully initialized {len(self.tracers)} tracers")

        except Exception as exc:
            self.logger.error(f"Tracers initialization failed: {exc}")
            raise

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
        self.logger.debug(f"Attempting to add tracer: {service.service_name}")

        if service.service_name in self.tracers or service in self.tracers.values():
            self.logger.error(
                f"Tracer addition failed: tracer '{
                    service.service_name
                }' already exists"
            )
            raise TracerAlreadyExistsError(
                f"Tracer with name '{
                    service.service_name
                }' or '{service}' already exists"
            )

        self.tracers[service.service_name] = service
        self.logger.info(f"Successfully added tracer: {service.service_name}")

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
        self.logger.debug(f"Attempting to remove tracer: {service_name}")

        if service_name not in self.tracers:
            self.logger.error(f"Tracer removal failed: '{service_name}' not found")
            raise TracerNotFoundError(
                f"Tracer with name '{service_name}' does not exist"
            )

        self.tracers.pop(service_name)
        self.logger.info(f"Successfully removed tracer: {service_name}")

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
        self.logger.debug(f"Retrieving tracer: {service_name}")

        if service_name not in self.tracers:
            self.logger.error(f"Tracer retrieval failed: '{service_name}' not found")
            raise TracerNotFoundError(
                f"Tracer with name '{service_name}' does not exist"
            )

        tracer = self.tracers[service_name]
        self.logger.debug(f"Successfully retrieved tracer: {service_name}")
        return tracer
