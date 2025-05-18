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


class ApplicationManager:
    """
    Основной класс для управления приложением FastAPI.

    Обеспечивает функциональность для инициализации приложения FastAPI
    с различными компонентами,
    включая трассировку, проверку здоровья и метрики.
    Управляет жизненным циклом приложения
    и его сервисов.
    """

    @inject
    def __init__(
        self,
        service_name: str,
        lifespan: Callable[[FastAPI], AsyncContextManager[None]] | None = None,
        table_manager: TableManager = Provide[Container.table_manager],
        tracer_manager: TracerManager = Provide[Container.tracer_manager],
        health_manager: HealthManager = Provide[Container.health_manager],
        lifecycle_manager: LifeCycleManager = Provide[Container.lifecycle_manager],
        metrics_manager: MetricsManager = Provide[Container.metrics_manager]
    ) -> None:
        """
        Инициализация менеджера приложения.

        Args:
            service_name: Имя сервиса
            console: Консоль для вывода информации
            lifespan: Функция жизненного цикла приложения
            tracer_manager: Менеджер трассировщиков
            health_manager: Менеджер проверки здоровья
            table_manager: Менеджер таблиц
            lifecycle_manager: Менеджер жизненного цикла
            metrics_manager: Менеджер метрик
        """
        self.app: FastAPI | None = None

        self._lifespan = lifespan
        self.service_name: str = service_name
        self._table_manager = table_manager
        self._tracer_manager = tracer_manager
        self._health_manager = health_manager
        self._lifecycle_manager = lifecycle_manager
        self._metrics_manager = metrics_manager

        self._initialized: bool = False

    async def __aenter__(self) -> "ApplicationManager":
        """
        Асинхронный контекстный менеджер для правильного использования ресурсов.

        Returns:
            ApplicationManager: текущий экземпляр
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Очистка ресурсов при выходе из контекстного менеджера.

        Закрывает все трейсеры и метрики.
        """

        tasks = [tracer.clean() for tracer in self._tracer_manager.tracers.values()]
        await asyncio.gather(*tasks)

        tasks = [service.clean() for service in self._metrics_manager.services.values()]
        await asyncio.gather(*tasks)

    def add_service(self, service: AbstractTracerService) -> None:
        """
        Добавляет сервис в менеджеры трассировки и здоровья.

        Args:
            service: Сервис для добавления
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
        Удаляет сервис из менеджеров трассировки и здоровья.

        Args:
            service: Сервис для удаления
        """
        try:
            self._tracer_manager.remove_tracer(service_name=service.service_name)
        except TracerNotFoundError as exc:
            raise exc
        try:
            self._health_manager.unregister_service(service=service)
        except ServiceNotFoundError as exc:
            raise exc

    @inject
    async def initialize_application(
        self, config: dict[str, Any],
        with_tracers: bool, with_metrics: bool,
        health_check: bool, storage: StorageVars = Provide[Container.storage]
    ) -> None:
        """
        Инициализирует приложение и его компоненты.

        Args:
            config: Конфигурация сервиса
            with_tracers: Включить трассировку
            with_health_check: Включить проверку здоровья
            with_metrics: Включить метрики

        Raises:
            Exception: Если возникла ошибка при инициализации
        """
        try:
            if health_check:
                healh_dict = await self._health_manager.check_services()
                storage['healh_dict'] = healh_dict

            storage['config'] = config

            self.app = self._lifecycle_manager.create_application()
            self._table_manager.display_tables(storage=storage)
        except ServiceNotFoundError as exc:
            self._table_manager.print_console(f"Found error: {exc.message}",
                                              style=Style(color='red', bold=True))
            raise exc
        try:
            if with_tracers:
                await self.__with_tracers()
        except Exception as exc:
            self._table_manager.print_console(f"Found error: {exc}",
                                              style=Style(color='red', bold=True))

        try:
            if with_metrics:
                await self.__with_metrics()
        except ServiceNotFoundError as exc:
            raise exc

        self._initialized = True

    @property
    def get_app(self) -> FastAPI:
        """
        Возвращает инициализированное приложение FastAPI.

        Returns:
            FastAPI: Экземпляр приложения

        Raises:
            ValueError: Если приложение не инициализировано
        """
        if self.app is None:
            raise ValueError("Application not initialized")
        return self.app

    def run(self, host: str, port: int, reload: bool) -> None:
        """
        Запускает приложение FastAPI.

        Args:
            host: Хост для запуска
            port: Порт для запуска
            reload: Перезагружать приложение при изменениях
        """
        if not self._initialized:
            raise ApplicationNotInitializedError('Application is not ibnitialized.')

        import uvicorn

        self._table_manager.print_console(
            f"Starting application at http://{host}:{port}",
            style=Style(bold=True, color='red')
        )

        uvicorn.run(
            app=f"{self.__module__}:app",
            host=host,
            port=port,
            reload=reload,
        )

    async def __with_tracers(self) -> None:
        await self._tracer_manager.initialize_tracers()
        FastAPIInstrumentor.instrument_app(self.app)  # type: ignore

    async def __with_metrics(self) -> None:
        await self._metrics_manager.initialize_services()
