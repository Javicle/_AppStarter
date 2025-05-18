import abc
from typing import Any, Generic, Mapping, Protocol, runtime_checkable

from rich.table import Table

from openverse_applaunch.objects.abc.heath import THeatlhResult
from openverse_applaunch.objects.abc.service import TService
from openverse_applaunch.objects.types import TSorH


@runtime_checkable
class TableConfigProtocol(Protocol):
    "Protocol that defines base settings for creating Table"

    title: str
    title_style: str
    show_header: bool
    header_style: str
    show_border: bool
    border_style: str
    padding: int
    expand: bool


class IManager(abc.ABC, Generic[TSorH]):
    """Base interface for Manager"""

    @abc.abstractmethod
    def register_service(self, service: TSorH) -> None: ...

    @abc.abstractmethod
    def unregister_service(self, service: TSorH) -> None: ...

    @abc.abstractmethod
    def get_service(self, service_name: str) -> TSorH: ...


class IHealthManager(IManager[TService], Generic[TService, THeatlhResult]):
    """Base interface for HealthManager"""

    @abc.abstractmethod
    async def check_service(self, service_name: str) -> THeatlhResult: ...

    @abc.abstractmethod
    async def check_services(self) -> Mapping[str, THeatlhResult]: ...


class IMetricsManager(IManager[TSorH]):
    """Base interface for MetricsManager"""


@runtime_checkable
class ITableCreator(Protocol):
    """Base interface for TableCreator"""

    def create_table(self, table_config: TableConfigProtocol) -> Table: ...


@runtime_checkable
class ITableRender(Protocol):
    "Interface for further realize TableRender"

    def populate_table(self, table: Table, *args: Any, **kwargs: Any) -> Table: ...


class ITableManager(abc.ABC):
    "Interface for TableManager"
