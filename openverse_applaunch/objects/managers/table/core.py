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
    Realize convenient methods for table managers
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
        if (
            name in self.table_creators_registry or 
            name in self.table_renders_registry or
            name in self.table_config_settings_registry
        ):
            raise TableError(f'Object with name: {name} already exists')

        if isinstance(table_obj, ITableCreator):
            self.table_creators_registry[name] = table_obj
        elif isinstance(table_obj, ITableRender):
            self.table_renders_registry[name] = table_obj
        elif isinstance(table_obj, TableConfigProtocol):
            self.table_config_settings_registry[name] = table_obj
        else:
            raise TableError(f'Unknown object type for: {name}')

    def remove(self, name: str) -> None:
        removed_any = False

        if name in self.table_creators_registry:
            del self.table_creators_registry[name]
            removed_any = True

        if name in self.table_renders_registry:
            del self.table_renders_registry[name]
            removed_any = True

        if name in self.table_config_settings_registry:
            del self.table_config_settings_registry[name]
            removed_any = True

        if not removed_any:
            raise TableError(f'Table with name: {name} not found')

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
        self, console: Console,
        utils_manager: UtilsManager,
    ) -> None:
        """
        Инициализация менеджера таблиц.

        Args:
            service_name: Имя сервиса для отображения в таблицах
            console: Консоль для вывода таблиц
            utils_manager: Менеджер утилит для работы с таблицами
        """
        self.console = console
        self.utils_manager = utils_manager

    def register_service(
        self, name: str, some_obj: ITableRender | ITableCreator | TableConfigProtocol
    ) -> None:
        """Регистрирует сервис в менеджере утилит."""
        self.utils_manager.add(name=name, table_obj=some_obj)

    def remove_service(self, name: str) -> None:
        """Удаляет сервис из менеджера утилит."""
        self.utils_manager.remove(name=name)

    def create_table(self, table_name: str,
                     table_data: dict[str, Any] | None = None) -> Table:
        """Создает таблицу с указанным именем и данными."""
        self._validate_table_components(table_name)
        table_creator = self.utils_manager.get_creator(name=table_name)
        table_render = self.utils_manager.get_render(name=table_name)
        table_config = self.utils_manager.get_config(table_name)

        table = table_creator.create_table(table_config=table_config)

        if table_data:
            # Передаем данные в render для заполнения таблицы
            table_render.populate_table(table=table, data=table_data)

        return table

    def print_console(self, text: str, style: Style) -> None:
        """Выводит текст в консоль с указанным стилем."""
        self.console.print(text, style=style)

    def display_tables(self, storage: StorageVars,
                       output: bool = False) -> dict[str, Table] | str:
        """Отображает все зарегистрированные таблицы."""
        tables: dict[str, Table] = {}

        for name in self.utils_manager.table_creators_registry.keys():
            self._validate_table_components(name=name)
            table_creator = self.utils_manager.get_creator(name)
            table = self._create_populate_table(
                name=name,
                table_creator=table_creator,
                storage=storage
            )
            tables[name] = table

        if output:
            with self.console.capture() as capture:
                for table in tables.values():
                    self.console.print(table)
            return capture.get()
        else:
            for table in tables.values():
                print(f'Table: {table.title}')
                self.console.print(table)
            return tables

    def _create_populate_table(self, name: str, storage: StorageVars,
                               table_creator: ITableCreator) -> Table:
        """Создает и заполняет таблицу данными."""
        creator_table = table_creator.create_table(
            table_config=self.utils_manager.get_config(name)
        )
        render_table = self.utils_manager.get_render(name)
        storage[name] = creator_table

        execute_dynamic_func(
            function=render_table.populate_table,
            available_args=storage
        )
        return creator_table

    def _validate_registries(self) -> None:
        """Проверяет, что все необходимые реестры заполнены."""
        if not self.utils_manager.table_creators_registry:
            raise TableError("No classes TableCreating were added")

        if not self.utils_manager.table_renders_registry:
            raise TableError("No classes TableRendering were added")
        
        if not self.utils_manager.table_config_settings_registry:
            raise TableError("No classes TableConfig were added")

    def _validate_table_components(self, name: str) -> None:
        """Проверяет наличие всех компонентов таблицы с указанным именем."""
        if name not in self.utils_manager.table_renders_registry:
            raise TableError(f"Not found class TableRender with {name}")
        if name not in self.utils_manager.table_config_settings_registry:
            raise TableError(f"Not found class TableConfig with {name}")
        if name not in self.utils_manager.table_creators_registry:
            raise TableError(f'Not found class TableCreator with {name}')