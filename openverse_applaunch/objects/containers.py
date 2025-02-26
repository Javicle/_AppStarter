from dependency_injector import containers, providers
from rich.console import Console

from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.table import TableManager
from openverse_applaunch.objects.managers.tracer import TracerManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    console: providers.Singleton[Console] = providers.Singleton(Console)
    tracer_manager: providers.Singleton[TracerManager] = providers.Singleton(TracerManager)
    health_manager = providers.Singleton(HealthManager)
    table_manager = providers.Singleton(TableManager, service_name=config.service_name)
    lifecycle_manager = providers.Singleton(LifeCycleManager, service_name=config.service_name)
