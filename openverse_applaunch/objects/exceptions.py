from typing import Any


class ManagerBaseException(Exception):
    """Базовое исключение для всех менеджеров"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class HealthManagerError(ManagerBaseException):
    """Исключения для HealthManager"""


class ServiceNotFoundError(HealthManagerError):
    """Сервис не найден"""


class ServiceAlreadyExistsError(HealthManagerError):
    """Сервис уже существует"""


class TracerManagerError(ManagerBaseException):
    """Исключения для TracerManager"""


class TracerNotFoundError(TracerManagerError):
    """Трейсер не найден"""


class TracerAlreadyExistsError(TracerManagerError):
    """Трейсер уже существует"""


class TableManagerError(ManagerBaseException):
    """Исключения для TableManager"""


class ConfigurationError(TableManagerError):
    """Ошибка конфигурации"""


class LifeCycleManagerError(ManagerBaseException):
    """Исключения для LifeCycleManager"""


class ApplicationNotInitializedError(LifeCycleManagerError):
    """Приложение не инициализировано"""
