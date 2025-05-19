"""
This core module for table manager
"""
from dataclasses import dataclass
from typing import Any, ClassVar, MutableMapping

from rich.console import Console
from rich.style import Style
from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    ITableRender,
    TableConfigProtocol,
)
from openverse_applaunch.objects.exceptions import TableError
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.services.dynamic_create import execute_dynamic_func


@dataclass()
class UtilsManager:
    """
    Realize convient methods table managers
    """
    table_creators_registry: ClassVar[
        MutableMapping[str, ITableCreator]
    ] = {}
    table_renders_registry: ClassVar[
        MutableMapping[str, ITableRender]
    ] = {}
    table_config_settings_registry: ClassVar[
        MutableMapping[str, TableConfigProtocol]
    ] = {}

    def get_creator(self, name: str) -> ITableCreator:
        try:
            return self.table_creators_registry[name]
        except KeyError:
            raise TableError(f'Not found table creator: {name}')

    def get_render(self, name: str) -> ITableRender:
        try:
            return self.table_renders_registry[name]
        except KeyError:
            raise TableError(f'Not found table render: {name}')

    def get_config(self, name: str) -> TableConfigProtocol:
        try:
            return self.table_config_settings_registry[name]
        except KeyError:
            raise TableError(f'Not found table config: {name}')

    def add(self, name: str, table_obj: (
        ITableCreator | TableConfigProtocol | ITableRender
    )) -> None:
        try:
            if isinstance(table_obj, ITableCreator):
                self.table_creators_registry[name] = table_obj
            elif isinstance(table_obj, ITableRender):
                self.table_renders_registry[name] = table_obj
            else:
                self.table_config_settings_registry[name] = table_obj
        except KeyError as exc:
            raise TableError(f'Object with name: {name} has exists : {exc}')

    def remove(self, name: str) -> None:
        try:
            del self.table_config_settings_registry[name]
            del self.table_creators_registry[name]
            del self.table_renders_registry[name]
        except KeyError as exc:
            raise TableError(f'Table with name: {name} has not delete: {exc}')

    def __str__(self) -> str:
        return str({
            "creators": self.table_creators_registry,
            "renders": self.table_renders_registry,
            "config": self.table_config_settings_registry,
        })


class TableManager:
    """
    Менеджер для создания и отображения таблиц с информацией о сервисе.

    Создает красиво отформатированные таблицы для вывода в консоль.
    """

    def __init__(
        self, service_name: str,
        console: Console,
        utils_manager: UtilsManager,
    ) -> None:
        """
        Инициализация менеджера таблиц.

        Args:
            service_name: Имя сервиса для отображения в таблицах
            console: Консоль для вывода таблиц
        """
        self.service_name = service_name
        self.console = console
        self.utils_manager = utils_manager

    def register_service(
        self, name: str, object: ITableRender | ITableCreator | TableConfigProtocol
    ) -> None:
        self.utils_manager.add(name=name, table_obj=object)

    def remove_service(self, name: str) -> None:
        self.utils_manager.remove(name=name)

    def create_table(self, table_name: str, table_data: dict[str, Any]) -> Table:

        self._validate_table_components(table_name)
        table_creator = self.utils_manager.get_creator(name=table_name)
        table_render = self.utils_manager.get_render(name=table_name)
        table_config = self.utils_manager.get_config(table_name)
        table = table_creator.create_table(table_config=table_config)
        if table_data:
            table_render.populate_table(table=table)
        return table

    def print_console(self, text: str, style: Style) -> None:
        self.console.print(text, style=style)

    def display_tables(self, storage: StorageVars,
                       output: bool = False) -> dict[str, Table] | str:

        tables: dict[str, Table] = {}
        for name, table_creator in self.utils_manager.table_creators_registry.items():
            self._validate_table_components(name=name)
            table = self._create_populate_table(
                name=name,
                table_creator=table_creator,
                storage=storage
            )
            tables[name] = table

        if output:
            with self.console.capture() as capture:
                self.console.print(table for table in tables)
            output_value = capture.get()
            return output_value
        else:
            return tables

    def _create_populate_table(self, name: str, storage: StorageVars,
                               table_creator: ITableCreator) -> Table:
        creator_table = table_creator.create_table(
            table_config=self.utils_manager.get_config(name)
        )
        render_table = self.utils_manager.get_render(name)
        storage[name] = creator_table
        execute_dynamic_func(function=render_table.populate_table,
                             available_args=storage)
        return creator_table

    def _validate_registries(self) -> None:
        if not self.utils_manager.table_creators_registry:
            raise TableError("No classes TableCreating were added")

        if not self.utils_manager.table_renders_registry:
            raise TableError("No classes TableRendering were added")

    def _validate_table_components(self, name: str) -> None:
        if not self.utils_manager.table_renders_registry[name]:
            raise TableError(f"Not found class TableRender with {name}")
        if not self.utils_manager.table_config_settings_registry[name]:
            raise TableError(f"Not found class TableConfig with {name}")
        if not self.utils_manager.table_creators_registry[name]:
            raise TableError(f'Not found class TableCreator with {name}')

