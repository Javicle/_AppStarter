from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    TableConfigProtocol,
)
from openverse_applaunch.objects.managers.table.registry import register_table_creator


@register_table_creator("main")
class MainTableCreater(ITableCreator):
    """
    Class for creating tables for showing config information of server

    Returns:
        Table: information table for library 'rich'
    """
    def create_table(self, table_config: TableConfigProtocol) -> Table:
        table = Table(
            show_header=table_config.show_header,
            title=table_config.title,
            title_style=table_config.title_style,
            border_style=table_config.border_style,
            header_style=table_config.header_style,
        )
        table.add_column("Parameter", style="cyan", justify="right")
        table.add_column("Value", style="green")
        return table

