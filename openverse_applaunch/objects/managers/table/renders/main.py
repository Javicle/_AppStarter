from typing import Any

from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import ITableRender
from openverse_applaunch.objects.managers.table.registry import register_table_render


@register_table_render("main")
class MainTableRender(ITableRender):
    def populate_table(self, table: Table, config: dict[str, Any]) -> Table:
        for attr_key, attr_value in config.items():
            table.add_row(attr_key, str(attr_value))
        return table
