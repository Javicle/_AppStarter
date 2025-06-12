"""
This core module for table manager
"""

from dataclasses import dataclass
from typing import Any, ClassVar, MutableMapping

from rich.console import Console
from rich.style import Style
from rich.table import Table
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    ITableRender,
    TableConfigProtocol,
)
from openverse_applaunch.objects.exceptions import TableError
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.services.dynamic_create import execute_dynamic_func

# Configure logger
logger = setup_logger(__name__)


@dataclass()
class UtilsManager:
    """
    Provides convenient methods for table managers.

    This class manages registries for table creators, renders, and configurations,
    providing methods to add, retrieve, and remove table components.
    """

    table_creators_registry: ClassVar[MutableMapping[str, ITableCreator]] = {}
    table_renders_registry: ClassVar[MutableMapping[str, ITableRender]] = {}
    table_config_settings_registry: ClassVar[
        MutableMapping[str, TableConfigProtocol]
    ] = {}

    def get_creator(self, name: str) -> ITableCreator:
        """
        Retrieve a table creator by name.

        Args:
            name: The name of the table creator to retrieve

        Returns:
            ITableCreator: The requested table creator

        Raises:
            TableError: If the table creator is not found
        """
        try:
            creator = self.table_creators_registry[name]
            logger.debug(f"Retrieved table creator: {name}")
            return creator
        except KeyError:
            logger.error(f"Table creator not found: {name}")
            raise TableError(f"Not found table creator: {name}")

    def get_render(self, name: str) -> ITableRender:
        """
        Retrieve a table render by name.

        Args:
            name: The name of the table render to retrieve

        Returns:
            ITableRender: The requested table render

        Raises:
            TableError: If the table render is not found
        """
        try:
            render = self.table_renders_registry[name]
            logger.debug(f"Retrieved table render: {name}")
            return render
        except KeyError:
            logger.error(f"Table render not found: {name}")
            raise TableError(f"Not found table render: {name}")

    def get_config(self, name: str) -> TableConfigProtocol:
        """
        Retrieve a table configuration by name.

        Args:
            name: The name of the table configuration to retrieve

        Returns:
            TableConfigProtocol: The requested table configuration

        Raises:
            TableError: If the table configuration is not found
        """
        try:
            config = self.table_config_settings_registry[name]
            logger.debug(f"Retrieved table config: {name}")
            return config
        except KeyError:
            logger.error(f"Table config not found: {name}")
            raise TableError(f"Not found table config: {name}")

    def add(
        self, name: str, table_obj: ITableCreator | TableConfigProtocol | ITableRender
    ) -> None:
        """
        Add a table object to the appropriate registry.

        Args:
            name: The name to register the object under
            table_obj: The table object to register (creator, render, or config)

        Raises:
            TableError: If an object with the same name already exists
            or if the object type is unknown
        """
        if (
            table_obj in self.table_creators_registry.values() or
            table_obj in self.table_renders_registry.values() or
            table_obj in self.table_config_settings_registry.values() 
        ):
            logger.error(f"Attempt to add duplicate object: {name}")
            raise TableError(f"Object with name: {name} already exists")

        if isinstance(table_obj, ITableCreator):
            self.table_creators_registry[name] = table_obj
            logger.info(f"Added table creator: {name}")
        elif isinstance(table_obj, ITableRender):
            self.table_renders_registry[name] = table_obj
            logger.info(f"Added table render: {name}")
        elif isinstance(table_obj, TableConfigProtocol):
            self.table_config_settings_registry[name] = table_obj
            logger.info(f"Added table config: {name}")
        else:
            logger.error(f"Unknown object type for: {name}")
            raise TableError(f"Unknown object type for: {name}")

    def remove(self, name: str) -> None:
        """
        Remove a table object from all registries.

        Args:
            name: The name of the object to remove

        Raises:
            TableError: If no object with the given name is found
        """
        removed_any = False

        if name in self.table_creators_registry:
            self.table_creators_registry.pop(name)
            removed_any = True
            logger.info(f"Removed table creator: {name}")

        if name in self.table_renders_registry:
            self.table_renders_registry.pop(name)
            removed_any = True
            logger.info(f"Removed table render: {name}")

        if name in self.table_config_settings_registry:
            self.table_config_settings_registry.pop(name)
            removed_any = True
            logger.info(f"Removed table config: {name}")

        if not removed_any:
            logger.error(f"Attempted to remove non-existent table: {name}")
            raise TableError(f"Table with name: {name} not found")

    def __str__(self) -> str:
        """
        Return string representation of all registries.

        Returns:
            str: String representation of creators, renders, and config registries
        """
        return str(
            {
                "creators": self.table_creators_registry,
                "renders": self.table_renders_registry,
                "config": self.table_config_settings_registry,
            }
        )


class TableManager:
    """
    Manager for creating and displaying service information tables.

    Creates beautifully formatted tables for console output using the Rich library.
    Manages table creators, renders, and configurations through a utility manager.
    """

    def __init__(
        self,
        console: Console,
        utils_manager: UtilsManager,
    ) -> None:
        """
        Initialize the table manager.

        Args:
            console: Console instance for table output
            utils_manager: Utility manager for handling table components
        """
        self.console = console
        self.utils_manager = utils_manager
        logger.info("TableManager initialized")

    def register_service(
        self, name: str, some_obj: ITableRender | ITableCreator | TableConfigProtocol
    ) -> None:
        """
        Register a service in the utility manager.

        Args:
            name: The name to register the service under
            some_obj: The service object to register
        """
        logger.info(f"Registering service: {name}")
        self.utils_manager.add(name=name, table_obj=some_obj)

    def remove_service(self, name: str) -> None:
        """
        Remove a service from the utility manager.

        Args:
            name: The name of the service to remove
        """
        logger.info(f"Removing service: {name}")
        self.utils_manager.remove(name=name)

    def create_table(
        self, table_name: str, table_data: dict[str, Any] | None = None
    ) -> Table:
        """
        Create a table with the specified name and data.

        Args:
            table_name: The name of the table to create
            table_data: Optional data to populate the table with

        Returns:
            Table: The created and optionally populated table
        """
        logger.info(f"Creating table: {table_name}")
        self._validate_table_components(table_name)
        table_creator = self.utils_manager.get_creator(name=table_name)
        table_render = self.utils_manager.get_render(name=table_name)
        table_config = self.utils_manager.get_config(table_name)

        table = table_creator.create_table(table_config=table_config)
        logger.debug(f"Table structure created for: {table_name}")

        if table_data:
            # Pass data to render for table population
            table_render.populate_table(table=table, data=table_data)
            logger.debug(f"Table populated with data for: {table_name}")

        return table

    def print_console(self, text: str, style: Style) -> None:
        """
        Output text to console with specified style.

        Args:
            text: The text to output
            style: The style to apply to the text
        """
        logger.debug(f"Printing to console: {text[:50]}...")
        self.console.print(text, style=style)

    def display_tables(
        self, storage: StorageVars, output: bool = False
    ) -> dict[str, Table] | str:
        """
        Display all registered tables.

        Args:
            storage: Storage variables for table data
            output: If True, return captured output as string;
            if False, print tables and return dict

        Returns:
            dict[str, Table] | str: Dictionary of tables or captured output string
        """
        logger.info("Displaying all registered tables")
        tables: dict[str, Table] = {}

        logger.debug("Table Creators: %s", self.utils_manager.table_creators_registry)
        logger.debug("Table Renders: %s", self.utils_manager.table_renders_registry)
        logger.debug(
            "Table Config: %s", self.utils_manager.table_config_settings_registry
        )

        for name in self.utils_manager.table_creators_registry.keys():
            logger.debug(f"Processing table: {name}")
            self._validate_table_components(name=name)
            table_creator = self.utils_manager.get_creator(name)
            table = self._create_populate_table(
                name=name, table_creator=table_creator, storage=storage
            )
            tables[name] = table
            logger.debug(f"Table created and populated: {name}")

        if output:
            logger.info("Capturing table output as string")
            with self.console.capture() as capture:
                for table in tables.values():
                    self.console.print(table)
            return capture.get()
        else:
            logger.info("Printing tables to console")
            for table in tables.values():
                logger.info(f"Displaying table: {table.title}")
                self.console.print(table)
            return tables

    def _create_populate_table(
        self, name: str, storage: StorageVars, table_creator: ITableCreator
    ) -> Table:
        """
        Create and populate a table with data.

        Args:
            name: The name of the table
            storage: Storage variables for table data
            table_creator: The table creator instance

        Returns:
            Table: The created and populated table
        """
        logger.debug(f"Creating and populating table: {name}")
        creator_table = table_creator.create_table(
            table_config=self.utils_manager.get_config(name)
        )
        render_table = self.utils_manager.get_render(name)
        storage["table"] = creator_table

        execute_dynamic_func(
            function=render_table.populate_table, available_args=storage
        )
        logger.debug(f"Table populated successfully: {name}")
        return creator_table

    def _validate_registries(self) -> None:
        """
        Validate that all necessary registries are populated.

        Raises:
            TableError: If any required registry is empty
        """
        logger.debug("Validating registries")

        if not self.utils_manager.table_creators_registry:
            logger.error("No table creators registered")
            raise TableError("No classes TableCreating were added")

        if not self.utils_manager.table_renders_registry:
            logger.error("No table renders registered")
            raise TableError("No classes TableRendering were added")

        if not self.utils_manager.table_config_settings_registry:
            logger.error("No table configs registered")
            raise TableError("No classes TableConfig were added")

        logger.debug("All registries validated successfully")

    def _validate_table_components(self, name: str) -> None:
        """
        Validate the presence of all table components with the specified name.

        Args:
            name: The name of the table to validate

        Raises:
            TableError: If any required component is missing
        """
        logger.debug(f"Validating table components for: {name}")

        if name not in self.utils_manager.table_renders_registry:
            logger.error(f"Missing table render for: {name}")
            raise TableError(f"Not found class TableRender with {name}")

        if name not in self.utils_manager.table_config_settings_registry:
            logger.error(f"Missing table config for: {name}")
            raise TableError(f"Not found class TableConfig with {name}")

        if name not in self.utils_manager.table_creators_registry:
            logger.error(f"Missing table creator for: {name}")
            raise TableError(f"Not found class TableCreator with {name}")

        logger.debug(f"All components validated for table: {name}")
