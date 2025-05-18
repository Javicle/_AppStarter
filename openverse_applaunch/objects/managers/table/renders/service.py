from rich.table import Table

from openverse_applaunch.objects.abc.interfaces import ITableRender
from openverse_applaunch.objects.enum import Color, ServiceStatus
from openverse_applaunch.objects.managers.table.registry import register_table_render
from openverse_applaunch.objects.models.health import HealthCheckDict


@register_table_render("service")
class ServiceTableRender(ITableRender):
    def populate_table(self, table: Table, health_dict: HealthCheckDict) -> Table:
        for service_name, health_result in health_dict.items():
            status_style = {
                ServiceStatus.HEALTHY: Color.GREEN.value,
                ServiceStatus.UNHEALTHY: Color.RED.value,
                ServiceStatus.UNKNOWN: Color.YELLOW.value,
            }.get(health_result.status, Color.WHITE.value)

            details_str = (
                "\n".join(f"{key}: {health_results_details}"
                          for key, health_results_details
                          in health_result.details.items())
                if health_result.details
                else "No details"
            )

            table.add_row(
                service_name,
                health_result.status.value,
                health_result.message or "No message",
                details_str,
                style=status_style,
            )

        return table

