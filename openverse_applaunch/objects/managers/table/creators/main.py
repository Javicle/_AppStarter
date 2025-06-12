from rich.table import Table
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    TableConfigProtocol,
)
from openverse_applaunch.objects.managers.table.registry import register_table_creator

# Configure logging
logger = setup_logger(__name__)


@register_table_creator("main")
class MainTableCreator(ITableCreator):
    def create_table(self, table_config: TableConfigProtocol) -> Table:
        logger.debug("Creating main information table")
        table = Table(
            show_header=table_config.show_header,
            title=table_config.title,
            title_style=table_config.title_style,
            border_style=table_config.border_style,
            header_style=table_config.header_style,
        )
        logger.debug("Adding columns to main table")
        table.add_column("Parameter", style="cyan", justify="right")
        table.add_column("Value", style="green")
        logger.info("Main table created successfully")
        return table
