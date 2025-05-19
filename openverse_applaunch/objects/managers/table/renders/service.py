from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import ITableRender
from openverse_applaunch.objects.enum import Color, ServiceStatus
from openverse_applaunch.objects.managers.table.registry import register_table_render
from openverse_applaunch.objects.models.health import HealthCheckDict


@register_table_render("service")
class ServiceTableRender(ITableRender):
    def populate_table(self, table: Table, health_dict: HealthCheckDict) -> Table:
        for service_name, health_result in health_dict.items():
            status_style = self._get_status_style(health_result.status)
            details_str = self._format_details(health_result.details)

            table.add_row(
                service_name,
                health_result.status.value,
                health_result.message or "No message",
                details_str,
                style=status_style,
            )
        return table

    def _get_status_style(self, status: ServiceStatus) -> str:
        return {
            ServiceStatus.HEALTHY: Color.GREEN.value,

            ServiceStatus.UNHEALTHY: Color.RED.value,
            ServiceStatus.UNKNOWN: Color.YELLOW.value,
        }.get(status, Color.WHITE.value)

    def _format_details(self, details: dict) -> str:
        if not details:
            return "No details"
        return "\n".join(f"{key}: {value_str}" for key, value_str in details.items())
