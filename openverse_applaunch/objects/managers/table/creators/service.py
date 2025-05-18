from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    TableConfigProtocol,
)
from openverse_applaunch.objects.constants import CENTER
from openverse_applaunch.objects.enum import Color
from openverse_applaunch.objects.managers.table.registry import register_table_creator


@register_table_creator("service")
class ServiceTableCreator(ITableCreator):
    def create_table(self, table_config: TableConfigProtocol) -> Table:

        table = Table(
            show_header=table_config.show_header,
            title=table_config.title,
            title_style=table_config.title_style,
            border_style=table_config.border_style,
            header_style=table_config.header_style,
        )

        table.add_column("Service", style=Color.PURPLE.value, justify=CENTER)
        table.add_column("Status", style=Color.WHITE.value, justify=CENTER)
        table.add_column("Detail", style=Color.WHITE.value, justify=CENTER)
        table.add_column("Additional Info", style=Color.WHITE.value, justify=CENTER)
        return table