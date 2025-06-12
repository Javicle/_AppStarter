from rich.table import Table
from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import ITableRender
from openverse_applaunch.objects.enum import Color, ServiceStatus
from openverse_applaunch.objects.managers.table.registry import register_table_render
from openverse_applaunch.objects.models.health import HealthCheckDict

# Configure logging
logger = setup_logger(__name__)


@register_table_render("service")
class ServiceTableRender(ITableRender):
    def populate_table(self, table: Table, health_dict: HealthCheckDict) -> Table:
        logger.debug(f"Populating service table with {len(health_dict)} services")
        for service_name, health_result in health_dict.items():
            logger.debug(f"Processing service: {service_name}")
            status_style = self._get_status_style(health_result.status)
            details_str = self._format_details(health_result.details)

            logger.debug(
                f"Adding row for {service_name} with status {health_result.status}"
            )
            table.add_row(
                service_name,
                health_result.message or "No message",
                details_str,
                style=status_style,
            )
        logger.info("Service table populated successfully")
        return table

    def _get_status_style(self, status: ServiceStatus) -> str:
        logger.debug(f"Getting style for status: {status}")
        return {
            ServiceStatus.HEALTHY: Color.GREEN.value,
            ServiceStatus.UNHEALTHY: Color.RED.value,
            ServiceStatus.UNKNOWN: Color.YELLOW.value,
        }.get(status, Color.WHITE.value)

    def _format_details(self, details: dict) -> str:
        logger.debug(f"Formatting details: {len(details) if details else 0} items")
        if not details:
            return "No details"
        return "\n".join(f"{key}: {value_str}" for key, value_str in details.items())
