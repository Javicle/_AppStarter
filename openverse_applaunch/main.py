"""
Основной модуль приложения, содержащий класс ApplicationManager.
"""

import asyncio
from types import TracebackType
from typing import Any, AsyncContextManager, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type:ignore
from rich.style import Style

from openverse_applaunch.objects.abc.service import AbstractTracerService
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.exceptions import (
    ApplicationNotInitializedError,
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


_container = Container()


class ApplicationManager:
    """
    Main class for managing a FastAPI application.

    Provides initialization, tracing, health checks, metrics,
    and lifecycle management for a FastAPI service.

    This class uses `dependency_injector` to supply manager
    instances for tables, tracing, health, lifecycle, and metrics.

    Public constructor: `.create(service_name, lifespan)`.

    Usage example:
        manager = ApplicationManager.create(
            service_name="user-service",
            lifespan=None,
        )
        await manager.initialize_application(
            config={"ENV": "prod"},
            with_tracers=True,
            with_metrics=False,
            health_check=True,
        )
        app = manager.get_app
        manager.run(host="0.0.0.0", port=8080, reload=True)
    """

    @inject
    def __init__(
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
            lifespan: Optional async context manager callback for FastAPI
                (e.g., application lifetime events). If `None`, no custom
                lifespan is used.
            table_manager: Manager that displays tables (injected).
            tracer_manager: Manager for OpenTelemetry tracers (injected).
            health_manager: Manager for health checks (injected).
            lifecycle_manager: Manager for FastAPI app lifecycle (injected).
            metrics_manager: Manager for metrics services (injected).
        """

        if not _allow_direct:
            raise ValueError(
                "Cannot be created ApplicationManager() directly"
                "Please use ApllicationManager.create"
            )
        self.app: FastAPI | None = None
        self._lifespan = lifespan
        self.service_name: str = service_name
        self._table_manager = table_manager
        self._tracer_manager = tracer_manager
        self._health_manager = health_manager
        self._lifecycle_manager = lifecycle_manager
        self._metrics_manager = metrics_manager
        self._initialized: bool = False

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

        Example:
            manager = ApplicationManager.create(
                service_name="order-service",
                lifespan=None
            )
        """
        _container.config.service_name.from_value(service_name)
        _container.wire(modules=[__name__])

        return cls(
            service_name=service_name,
            lifespan=lifespan,
            _allow_direct=True
        )

    async def __aenter__(self) -> "ApplicationManager":
        """
        Enter the async context manager.

        Returns:
            ApplicationManager: The same manager instance.

        Example:
            async with ApplicationManager.create("my-service") as manager:
                # manager is available within the block
                pass
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,  # type: ignore
        exc_val: BaseException | None,  # type: ignore
        exc_tb: TracebackType | None,  # type: ignore
    ) -> None:
        """
        Exit the async context manager, cleaning up resources.

        This will:
            - Call `.clean()` on all tracers.
            - Call `.clean()` on all initialized metrics services.

        Args:
            exc_type: Exception type if raised inside the context.
            exc_val: Exception instance if raised.
            exc_tb: Traceback of the exception if raised.
        """
        # Clean up all tracers concurrently
        tracer_tasks = [
            tracer.clean() for tracer in self._tracer_manager.tracers.values()
        ]
        await asyncio.gather(*tracer_tasks)

        # Clean up all metric services concurrently
        metric_tasks = [
            service.clean() for service in self._metrics_manager.services.values()
        ]
        await asyncio.gather(*metric_tasks)

    def add_service(self, service: AbstractTracerService) -> None:
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
        """
        try:
            self._tracer_manager.add_tracer(service)
        except TracerAlreadyExistsError as exc:
            raise exc

        try:
            self._health_manager.register_service(service)
        except ServiceAlreadyExistsError as exc:
            raise exc

    def delete_service(self, service: AbstractTracerService) -> None:
        """
        Remove an existing service from tracing and health managers.

        Args:
            service: The service instance to remove.

        Raises:
            TracerNotFoundError: If no tracer with this service name exists.
            ServiceNotFoundError: If the health manager does not recognize it.
        """
        try:
            self._tracer_manager.remove_tracer(
                service_name=service.service_name
            )
        except TracerNotFoundError as exc:
            raise exc

        try:
            self._health_manager.unregister_service(service=service)
        except ServiceNotFoundError as exc:
            raise exc

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

        This method performs the following steps:
            1. If `health_check` is True, perform health checks and store results.
            2. Store `config` in shared storage.
            3. Create the FastAPI app via `LifeCycleManager`.
            4. Display database or resource tables via `TableManager`.
            5. If `with_tracers` is True, initialize and instrument trackers.
            6. If `with_metrics` is True, initialize metric services.
            7. Set `_initialized = True` upon success.

        Args:
            config: A dictionary of application configuration values.
            with_tracers: If True, initialize and instrument OpenTelemetry tracers.
            with_metrics: If True, initialize metrics-collection services.
            health_check: If True, run health checks on registered services.
            storage: A shared dict for passing data between managers.

        Raises:
            ServiceNotFoundError: If a service required during initialization
                is not found anywhere.
            Exception: On any other initialization failure.
        """
        try:
            if health_check:
                health_dict = await self._health_manager.check_services()
                storage["health_dict"] = health_dict

            storage["config"] = config
            self.app = self._lifecycle_manager.create_application()
            self._table_manager.display_tables(storage=storage)
        except ServiceNotFoundError as exc:
            self._table_manager.print_console(
                f"Found error: {exc.message}",
                style=Style(color="red", bold=True),
            )
            raise exc

        # Initialize tracers if requested
        try:
            if with_tracers:
                await self.__with_tracers()
        except Exception as exc:
            self._table_manager.print_console(
                f"Found error during tracer initialization: {exc}",
                style=Style(color="red", bold=True),
            )

        # Initialize metrics if requested
        try:
            if with_metrics:
                await self.__with_metrics()
        except ServiceNotFoundError as exc:
            raise exc

        self._initialized = True

    @property
    def get_app(self) -> FastAPI:
        """
        Return the initialized FastAPI application instance.

        Raises:
            ValueError: If the application has not yet been initialized.

        Returns:
            FastAPI: The internal FastAPI application object.
        """
        if self.app is None:
            raise ValueError("Application not initialized")
        return self.app

    def run(self, host: str, port: int, reload: bool) -> None:
        """
        Start the FastAPI application with Uvicorn.

        This method prints a startup message and then calls `uvicorn.run`.
        It requires that `initialize_application` has already been called.

        Args:
            host: Host address (e.g., "127.0.0.1").
            port: Port number (e.g., 8000).
            reload: If True, enable auto-reload on code changes.

        Raises:
            ApplicationNotInitializedError: If `.initialize_application` was
                not called successfully before `.run`.
        """
        if not self._initialized:
            raise ApplicationNotInitializedError(
                "Application is not initialized."
            )

        import uvicorn

        self._table_manager.print_console(
            f"Starting application at http://{host}:{port}",
            style=Style(bold=True, color="red"),
        )
        uvicorn.run(
            app=f"{self.__module__}:app",
            host=host,
            port=port,
            reload=reload,
        )

    async def __with_tracers(self) -> None:
        """
        Private helper: Initialize all tracers and instrument the FastAPI app.

        Raises:
            Any exception raised by `TracerManager.initialize_tracers`.
        """
        await self._tracer_manager.initialize_tracers()
        FastAPIInstrumentor.instrument_app(self.app)  # type: ignore

    async def __with_metrics(self) -> None:
        """
        Private helper: Initialize all metrics-collection services.

        Raises:
            Any exception raised by `MetricsManager.initialize_services`.
        """
        await self._metrics_manager.initialize_services()
