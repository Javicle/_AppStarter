"""
Контейнеры зависимостей для внедрения зависимостей.
"""

from dependency_injector import containers, providers
from rich.console import Console

from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.metrics import MetricsManager
from openverse_applaunch.objects.managers.table.core import TableManager, UtilsManager
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.managers.tracer import TracerManager


class Container(containers.DeclarativeContainer):
    """
    Контейнер для внедрения зависимостей.

    Обеспечивает доступ к общим компонентам приложения.
    """

    config = providers.Configuration()

    console: providers.Singleton[Console] = providers.Singleton(Console)

    metrics_manager = providers.Singleton(MetricsManager, console=console)

    tracer_manager: providers.Singleton[TracerManager] = providers.Singleton(
        TracerManager
    )

    health_manager: providers.Singleton[
        HealthManager
    ] = providers.Singleton(HealthManager)

    utils_manager = providers.Singleton(UtilsManager)

    table_manager = providers.Singleton(
        TableManager, service_name=config.service_name,
        console=console, utils_manager=utils_manager
    )

    lifecycle_manager = providers.Singleton(
        LifeCycleManager, service_name=config.service_name
    )

    storage = providers.Singleton(StorageVars)

