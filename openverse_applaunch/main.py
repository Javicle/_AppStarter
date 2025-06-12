"""
Main application module containing the ApplicationManager class.

This module provides the core ApplicationManager class that orchestrates
FastAPI application initialization, tracing, health checks, metrics,
and lifecycle management.

Class: ApplicationManager

Responsibilities:
    - create: Public constructor to instantiate manager with DI hidden.
    - __aenter__/__aexit__: Support async context for automatic cleanup.
    - initialize_application: Set up FastAPI app, health, tracers, metrics.
    - add_service: Register a service for tracing and health checking.
    - delete_service: Unregister a service from tracing and health checking.
    - get_app: Property to retrieve initialized FastAPI application.
    - run: Launch the FastAPI app with Uvicorn.

Usage example:
    >>> from application_manager import ApplicationManager
    >>> import asyncio
    >>>
    >>> async def main():
    ...     # Create manager
    ...     manager = ApplicationManager.create(
    ...         service_name="user-service",
    ...         lifespan=None,
    ...     )
    ...     # Initialize application with tracers and health checks
    ...     await manager.initialize_application(
    ...         config={"ENV": "prod"},
    ...         with_tracers=True,
    ...         with_metrics=False,
    ...         health_check=True,
    ...     )
    ...     # Retrieve FastAPI app
    ...     app = manager.get_app
    ...     # Run the application
    ...     manager.run(host="0.0.0.0", port=8080, reload=True)
    >>>
    >>> asyncio.run(main())
"""

from typing import Any, AsyncContextManager, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type:ignore
from rich.style import Style
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.service import AbstractTracerService
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.exceptions import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
    TracerAlreadyExistsError,
    TracerNotFoundError,
)
from openverse_applaunch.objects.managers import (
    HealthManager,
    LifeCycleManager,
    MetricsManager,
    TableManager,
    TracerManager,
)
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.models.health import HealthCheckResult

# Configure logging
logger = setup_logger(__name__)
_container = Container()


class ApplicationManager:
    """
    Main class for managing a FastAPI application.

    Provides initialization, tracing, health checks, metrics,
    and lifecycle management for a FastAPI service.

    Methods:
        create: Public constructor hiding DI parameters.
        __aenter__: Enter async context for auto-cleanup.
        __aexit__: Exit async context and clean resources.
        add_service: Register a service for tracing and health.
        delete_service: Unregister a service from tracing and health.
        initialize_application: Set up FastAPI app and components.
        get_app: Return initialized FastAPI application.
        run: Launch the FastAPI application using Uvicorn.
    """

    @inject
    def __init__(  # noqa: WPS211
        self,
        service_name: str,
        lifespan: Callable[[FastAPI], AsyncContextManager[None]] | None = None,
        *,
        _allow_direct: bool = False,
        table_manager: TableManager = Provide[Container.table_manager],
        tracer_manager: TracerManager = Provide[Container.tracer_manager],
        health_manager: HealthManager = Provide[Container.health_manager],
        lifecycle_manager: LifeCycleManager = Provide[Container.lifecycle_manager],
        metrics_manager: MetricsManager = Provide[Container.metrics_manager],
    ) -> None:
        """
        Initialize an ApplicationManager instance.

        Note:
            This constructor is intended for dependency-injection only.
            Use the classmethod `create` to instantiate in application code.

        Args:
            service_name: Name of the service (e.g., "billing-service").
            lifespan: Optional async context manager for FastAPI.
                If `None`, no custom lifespan is used.
            _allow_direct: Internal flag to prevent direct instantiation.
            table_manager: Manager that displays tables (injected).
            tracer_manager: Manager for OpenTelemetry tracers (injected).
            health_manager: Manager for health checks (injected).
            lifecycle_manager: Manager for FastAPI app lifecycle (injected).
            metrics_manager: Manager for metrics services (injected).

        Raises:
            ValueError: If _allow_direct is False (direct instantiation not allowed)
        """
        if not _allow_direct:
            error_msg = (
                "Cannot create ApplicationManager() directly."
                "Please use ApplicationManager.create()"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Initializing ApplicationManager for service: {service_name}")

        self.app: FastAPI | None = None
        self._lifespan = lifespan
        self.service_name: str = service_name
        self._table_manager = table_manager
        self._tracer_manager = tracer_manager
        self._health_manager = health_manager
        self._lifecycle_manager = lifecycle_manager
        self._metrics_manager = metrics_manager
        self._initialized: bool = False

        logger.debug(f"Managers initialized for service: {service_name}")

        if self._lifespan:
            self._lifecycle_manager.lifespan = self._lifespan
            logger.debug("Custom lifespan callback configured")
        else:
            logger.debug("No custom lifespan callback provided")

    @classmethod
    def create(
        cls,
        service_name: str,
        lifespan: Callable[[FastAPI], AsyncContextManager[None]] | None = None,
    ) -> "ApplicationManager":
        """
        Public constructor for ApplicationManager.

        This method hides DI-specific parameters from the caller.
        It returns a new `ApplicationManager` with only two visible args.

        Args:
            service_name: Name of the service (e.g., "billing-service").
            lifespan: Optional async context manager for FastAPI.

        Returns:
            ApplicationManager: A new manager instance ready for DI injection.

        Raises:
            Exception: If dependency injection configuration fails.

        Usage example:
            >>> manager = ApplicationManager.create(
            ...     service_name="payment-service",
            ...     lifespan=None
            ... )
        """
        logger.info(f"Creating ApplicationManager for service: {service_name}")

        try:
            _container.config.service_name.from_value(service_name)
            _container.wire(modules=[__name__])
            logger.debug("Dependency injection container configured successfully")

            manager = cls(
                service_name=service_name, lifespan=lifespan, _allow_direct=True
            )

            logger.info(f"ApplicationManager created successfully for: {service_name}")
            return manager

        except Exception as exc:
            logger.error(
                f"Failed to create ApplicationManager for {service_name}: {exc}"
            )
            raise

    async def __aenter__(self) -> "ApplicationManager":
        """
        Enter the async context manager.

        Use this for automatic cleanup of tracers and metrics.

        Returns:
            ApplicationManager: The same manager instance.

        Usage example:
            >>> async with ApplicationManager.create("my-service") as manager:
            ...     # manager is available within the block
            ...     pass
        """
        logger.info(f"Entering async context for service: {self.service_name}")
        return self

    def add_service(self, service: AbstractTracerService[HealthCheckResult]) -> None:
        """
        Add a new service to the tracing and health managers.

        This method registers the given service with both:
            - `TracerManager` (adds a tracer for OpenTelemetry)
            - `HealthManager`  (registers it for health checks)

        Args:
            service: An instance that implements `AbstractTracerService`.

        Raises:
            TracerAlreadyExistsError: If a tracer with the same name exists.
            ServiceAlreadyExistsError: If the health manager already has it.

        Usage example:
            >>> from openverse_applaunch.objects.abc.service import MyService
            >>> service = MyService(service_name="my-service")
            >>> manager.add_service(service)
        """
        logger.info(f"Adding service: {service.service_name}")

        try:
            self._tracer_manager.add_tracer(service)
            logger.debug(f"Service {service.service_name} added to tracer manager")
        except TracerAlreadyExistsError as exc:
            logger.error(f"Tracer already exists for service {service.service_name}")
            raise exc

        try:
            self._health_manager.register_service(service)
            logger.debug(
                f"Service {service.service_name} registered with health manager"
            )
        except ServiceAlreadyExistsError as exc:
            logger.error(
                f"Service {service.service_name} already exists in health manager"
            )
            raise exc

        logger.info(f"Service {service.service_name} added successfully")

    def delete_service(self, service: AbstractTracerService) -> None:
        """
        Remove an existing service from tracing and health managers.

        Args:
            service: The service instance to remove.

        Raises:
            TracerNotFoundError: If no tracer with this service name exists.
            ServiceNotFoundError: If the health manager does not recognize it.

        Usage example:
            >>> from openverse_applaunch.objects.abc.service import MyService
            >>> service = MyService(service_name="my-service")
            >>> manager.delete_service(service)
        """
        logger.info(f"Deleting service: {service.service_name}")

        try:
            self._tracer_manager.remove_tracer(service_name=service.service_name)
            logger.debug(f"Service {service.service_name} removed from tracer manager")
        except TracerNotFoundError as exc:
            logger.error(f"Tracer not found for service {service.service_name}")
            raise exc

        try:
            self._health_manager.unregister_service(service=service)
            logger.debug(
                f"Service {service.service_name} unregistered from health manager"
            )
        except ServiceNotFoundError as exc:
            logger.error(f"Service {service.service_name} not found in health manager")
            raise exc

        logger.info(f"Service {service.service_name} deleted successfully")

    @inject
    async def initialize_application(
        self,
        config: dict[str, Any],
        with_tracers: bool,
        with_metrics: bool,
        health_check: bool,
        storage: StorageVars = Provide[Container.storage],
    ) -> None:
        """
        Initialize the FastAPI application and its components.

        Steps:
            1. If `health_check` is True, perform health checks and store results.
            2. Store `config` in shared storage.
            3. Create the FastAPI app via `LifeCycleManager`.
            4. Display resource tables via `TableManager`.
            5. If `with_tracers` is True, initialize and instrument tracers.
            6. If `with_metrics` is True, initialize metric services.
            7. Set `_initialized = True` upon success.

        Args:
            config: A dictionary of application configuration values.
            with_tracers: If True, initialize and instrument OpenTelemetry tracers.
            with_metrics: If True, initialize metrics-collection services.
            health_check: If True, run health checks on registered services.
            storage: A shared dict for passing data between managers.

        Raises:
            ServiceNotFoundError: If a service
            required during initialization is not found.
            Exception: On any other initialization failure.

        Usage example:
            >>> await manager.initialize_application(
            ...     config={"DB_URL": "postgres://..."},
            ...     with_tracers=True,
            ...     with_metrics=True,
            ...     health_check=True,
            ... )
        """
        logger.info(f"Initializing application for service: {self.service_name}")
        logger.debug(
            f"Configuration: tracers={with_tracers}, metrics={with_metrics}, "
            f"health_check={health_check}"
        )

        try:
            # Perform health checks if requested
            if health_check:
                logger.info("Performing health checks")
                health_dict = await self._health_manager.check_services()
                storage["health_dict"] = health_dict
                logger.info(f"Health checks completed for {len(health_dict)} services")
            else:
                logger.debug("Health checks skipped")

            # Store configuration
            storage["config"] = config
            logger.debug("Configuration stored with items %s", len(config))
            # logger.warning("STORAGE HAVE %s", storage)

            # Create FastAPI application
            logger.info("Creating FastAPI application")
            self.app = self._lifecycle_manager.create_application()
            logger.info("FastAPI application created successfully")

            # Display tables
            self.__import_modules()
            logger.info("Displaying resource tables")
            self._table_manager.display_tables(storage=storage)
            logger.debug("Resource tables displayed")

        except ServiceNotFoundError as exc:
            error_msg = f"Service not found during initialization: {exc.message}"
            logger.error(error_msg)
            self._table_manager.print_console(
                f"Found error: {exc.message}",
                style=Style(color="red", bold=True),
            )
            raise exc
        except Exception as exc:
            logger.error(f"Unexpected error during basic initialization: {exc}")
            raise

        if with_tracers:
            try:
                logger.info("Initializing tracers")
                await self.__with_tracers()
                logger.info("Tracers initialized successfully")
            except Exception as exc:
                error_msg = f"Error during tracer initialization: {exc}"
                logger.error(error_msg)
                self._table_manager.print_console(
                    error_msg,
                    style=Style(color="red", bold=True),
                )
        else:
            logger.debug("Tracer initialization skipped")

        if with_metrics:
            try:
                logger.info("Initializing metrics services")
                await self.__with_metrics()
                logger.info("Metrics services initialized successfully")
            except ServiceNotFoundError as exc:
                logger.error(
                    f"Service not found during metrics initialization: {exc.message}"
                )
                raise exc
            except Exception as exc:
                logger.error(f"Error during metrics initialization: {exc}")
                raise
        else:
            logger.debug("Metrics initialization skipped")

        self._initialized = True
        logger.info(
            f"Application initialization completed for service: {self.service_name}"
        )

    @property
    def get_app(self) -> FastAPI:
        """
        Return the initialized FastAPI application instance.

        Raises:
            ValueError: If the application has not yet been initialized.

        Returns:
            FastAPI: The internal FastAPI application object.

        Usage example:
            >>> app = manager.get_app
        """
        if self.app is None:
            error_msg = (
                "Application not initialized. Call initialize_application() first."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Returning initialized FastAPI application")
        return self.app

    async def __with_tracers(self) -> None:
        """
        Private helper: Initialize all tracers and instrument the FastAPI app.

        Raises:
            Any exception raised by `TracerManager.initialize_tracers`.
        """
        logger.debug("Initializing all tracers")

        try:
            await self._tracer_manager.initialize_tracers()
            logger.debug("Tracer manager initialization completed")

            if self.app is None:
                raise ValueError("FastAPI app not available for instrumentation")

            FastAPIInstrumentor.instrument_app(self.app)  # type: ignore
            logger.info("FastAPI application instrumented for tracing")

        except Exception as exc:
            logger.error(f"Failed to initialize tracers: {exc}")
            raise

    async def __with_metrics(self) -> None:
        """
        Private helper: Initialize all metrics-collection services.

        Raises:
            Any exception raised by `MetricsManager.initialize_services`.
        """
        logger.debug("Initializing all metrics services")

        try:
            await self._metrics_manager.initialize_services()
            logger.info("Metrics manager initialization completed")

        except Exception as exc:
            logger.error(f"Failed to initialize metrics services: {exc}")
            raise

    def run(self, host: str = "127.0.0.1",
            port: int = 8000, reload: bool = False) -> None:
        """
        Run the FastAPI application using Uvicorn.

        Args:
            host: Host address to bind to. Defaults to "127.0.0.1".
            port: Port to bind to. Defaults to 8000.
            reload: Whether to enable auto-reload. Defaults to False.

        Raises:
            ValueError: If the application is not initialized.

        Usage example:
            >>> manager.run(host="0.0.0.0", port=8080, reload=True)
        """
        if self.app is None:
            error_msg = "Cannot run; application not initialized."
            logger.error(error_msg)
            raise ValueError(error_msg)

        import uvicorn

        logger.info(f"Running application on {host}:{port} (reload={reload})")
        uvicorn.run(self.app, host=host, port=port, reload=reload)

    def __import_modules(self) -> None: 
        # this imports needs to work decorators.
        from openverse_applaunch.objects.managers.table.creators.main import ( # noqa: F401
            MainTableCreator,
        )
        from openverse_applaunch.objects.managers.table.creators.service import (  # noqa: F401 
            ServiceTableCreator, 
        )
        from openverse_applaunch.objects.managers.table.renders.main import (  # noqa: F401
            MainTableRender, 
        )
        from openverse_applaunch.objects.managers.table.renders.service import (  # noqa: F401
            ServiceTableRender,
        )
        from openverse_applaunch.objects.managers.table.storage import StorageVars  # noqa: F401
        from openverse_applaunch.objects.models.config import (  # noqa: F401
            ModernTableConfig,
            ReportTableConfig,
        )