from rich.table import Table
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    TableConfigProtocol,
)
from openverse_applaunch.objects.constants import CENTER
from openverse_applaunch.objects.enum import Color
from openverse_applaunch.objects.managers.table.registry import register_table_creator

# Configure logging
logger = setup_logger(__name__)


@register_table_creator("service")
class ServiceTableCreator(ITableCreator):
    def create_table(self, table_config: TableConfigProtocol) -> Table:
        logger.debug("Creating service status table")
        table = Table(
            show_header=table_config.show_header,
            title=table_config.title,
            title_style=table_config.title_style,
            border_style=table_config.border_style,
            header_style=table_config.header_style,
        )

        logger.debug("Adding columns to service table")
        table.add_column("Service", style=Color.PURPLE.value, justify=CENTER)
        table.add_column("Status", style=Color.WHITE.value, justify=CENTER)
        table.add_column("Detail", style=Color.WHITE.value, justify=CENTER)
        table.add_column("Additional Info", style=Color.WHITE.value, justify=CENTER)
        logger.info("Service table created successfully")
        return table
