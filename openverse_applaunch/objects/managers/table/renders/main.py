from typing import Any

from rich.table import Table
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import ITableRender
from openverse_applaunch.objects.managers.table.registry import register_table_render

# Configure logging
logger = setup_logger(__name__)


@register_table_render("main")
class MainTableRender(ITableRender):
    def populate_table(self, table: Table, config: dict[str, Any]) -> Table:
        logger.debug(f"Populating main table with {len(config)} config items")
        for attr_key, attr_value in config.items():
            logger.debug(f"Adding row: {attr_key}={attr_value}")
            table.add_row(attr_key, str(attr_value))
        return table
