from typing import AsyncContextManager, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type:ignore
from rich.console import Console

from openverse_applaunch.objects.base import AbstractTracerService, ServiceConfig
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.table import TableManager
from openverse_applaunch.objects.managers.tracer import TracerManager


class ApplicationManager:
    @inject
    def __init__(
        self,
        service_name: str,
        console: Console = Provide[Container.console],
        lifespan: Callable[[FastAPI], AsyncContextManager[None]] | None = None,
        tracer_manager: TracerManager = Provide[Container.tracer_manager],
        health_manager: HealthManager = Provide[Container.health_manager],
        table_manager: TableManager = Provide[Container.table_manager],
        lifecycle_manager: LifeCycleManager = Provide[Container.lifecycle_manager],
    ) -> None:
        self.app: FastAPI | None = None

        self.lifespan = lifespan
        self.console = console
        self.table_manager = table_manager
        self.tracer_manager = tracer_manager
        self.health_manager = health_manager
        self.service_name: str = service_name
        self.lifecycle_manager = lifecycle_manager

        self._initialized: bool = False

    def add_service(self, service: AbstractTracerService) -> None:
        try:
            self.tracer_manager.add_tracer(service.service_name, service)
            self.health_manager.register_service(service)
        except Exception as e:
            self.console.print(f"[bold red]Error registering service: {e}")

    def delete_service(self, service: AbstractTracerService) -> None:
        try:
            self.tracer_manager.remove_tracer(service_name=service.service_name)
            self.health_manager.unregister_service(service=service)
        except Exception as e:
            self.console.print(f"[bold red]Error deleting service: {e}")

    async def initialize_application(
        self, config: ServiceConfig, with_tracers: bool, with_health_check: bool
    ) -> None:
        try:

            self.app = self.lifecycle_manager.create_application()
            self.table_manager.create_main_table(config=config)
            if with_tracers:
                await self.tracer_manager.initialize_tracers()
                FastAPIInstrumentor.instrument_app(self.app)  # type: ignore

            if with_health_check:
                health_status = await self.health_manager.check_services()
                self.table_manager.create_check_services_table(health_dict=health_status)

        except Exception as e:
            self.console.print(f"[bold red]Error initializing application: {e}")
            raise e

    @property
    def get_app(self) -> FastAPI:
        if self.app is None:
            raise ValueError("Application not initialized")
        return self.app

    def run(self, host: str, port: int, reload: bool) -> None:
        import uvicorn

        uvicorn.run(
            app=f"{self.__module__}:app",
            host=host,
            port=port,
            reload=reload,
        )
