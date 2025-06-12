"""
Абстрактные базовые классы для различных типов сервисов.
"""

import abc
from typing import Any, Generic, MutableMapping, Protocol, TypeAlias, TypeVar

from openverse_applaunch.objects.abc.heath import THeatlhResult


class SuccessfulServiceProtocol(Protocol):
    response_time: float
    message: str


class FailedServiceProtocol(Protocol):
    response_time: float
    message: str


class OtherServiceProtocol(Protocol):
    response_time: float
    message: str


ServiceStatusResponseProtocol: TypeAlias = (
    SuccessfulServiceProtocol | FailedServiceProtocol | OtherServiceProtocol
)


class AbstractTracerService(abc.ABC, Generic[THeatlhResult]):
    """
    Абстрактный базовый класс для сервисов трассировки.

    Определяет общий интерфейс для всех сервисов трассировки в системе.
    """

    def __init__(self) -> None:
        self.service_name: str = "base_service"
        self._initialized: bool = False

    @abc.abstractmethod
    async def init(self, *args: Any, **kwargs: Any) -> None:
        """
        Инициализация сервиса трассировки.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы
        """
        self._initialized = True

    @abc.abstractmethod
    async def clean(self, *args: Any, **kwargs: Any) -> None:
        """
        Очистка ресурсов сервиса при завершении.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы
        """
        ...

    @abc.abstractmethod
    async def health_check(self, *args: Any, **kwargs: Any) -> THeatlhResult:
        """
        Проверка здоровья сервиса.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы

        Returns:
            HealthCheckResult: Результат проверки здоровья
        """
        ...


class AbstractMetricsService(abc.ABC, Generic[THeatlhResult]):
    """
    Абстрактный базовый класс для сервисов метрик.

    Определяет общий интерфейс для всех сервисов сбора метрик в системе.
    """

    service_name: str
    _initialized: bool = False

    @abc.abstractmethod
    async def init(self, *args: Any, **kwargs: Any) -> None:
        """
        Инициализация сервиса метрик.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы
        """
        type(self)._initialized = True

    @abc.abstractmethod
    async def clean(self, *args: Any, **kwargs: Any) -> None:
        """
        Очистка ресурсов сервиса при завершении.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы
        """
        ...

    @abc.abstractmethod
    async def health_check(self, *args: Any, **kwargs: Any) -> THeatlhResult:
        """
        Проверка здоровья сервиса метрик.

        Args:
            *args: Произвольные позиционные аргументы
            **kwargs: Произвольные именованные аргументы

        Returns:
            HealthCheckResult: Результат проверки здоровья
        """
        ...

    @abc.abstractmethod
    def create_counter(self, name: str, description: str, unit: str = "1") -> Any:
        """
        Создание счетчика для метрик.

        Args:
            name: Имя счетчика
            description: Описание счетчика
            unit: Единица измерения

        Returns:
            Any: Созданный счетчик
        """
        ...

    @abc.abstractmethod
    def create_histogram(self, name: str, description: str, unit: str = "ms") -> Any:
        """
        Создание гистограммы для метрик.

        Args:
            name: Имя гистограммы
            description: Описание гистограммы
            unit: Единица измерения

        Returns:
            Any: Созданная гистограмма
        """
        ...

    @abc.abstractmethod
    def create_gauge(self, name: str, description: str, unit: str = "1") -> Any:
        """
        Создание измерителя (gauge) для метрик.

        Args:
            name: Имя измерителя
            description: Описание измерителя
            unit: Единица измерения

        Returns:
            Any: Созданный измеритель
        """
        ...


class ServiceCheck(abc.ABC):
    """
    Абстрактный базовый класс для проверок сервисов.

    Позволяет создавать произвольные проверки здоровья для сервисов.
    """

    def __init__(self, service_name: str, **kwargs: Any) -> None:
        """
        Инициализация проверки сервиса.

        Args:
            service_name: Имя сервиса
            **kwargs: Дополнительные параметры для проверки
        """
        self.service_name = service_name
        self.kwargs = kwargs

    @abc.abstractmethod
    async def check(self) -> ServiceStatusResponseProtocol:
        """
        Выполнение проверки сервиса.

        Returns:
            ServiceStatusResponse: Результат проверки
        """
        ...


SomeAbstractServiceType = (
    AbstractMetricsService | AbstractTracerService
)

MetricsDictType: TypeAlias = MutableMapping[
    str, AbstractMetricsService
]
TracersDictType: TypeAlias = MutableMapping[
    str, AbstractTracerService
]


TService = TypeVar("TService", bound="SomeAbstractServiceType")
