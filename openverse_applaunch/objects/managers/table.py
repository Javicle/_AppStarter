from rich.console import Console
from rich.table import Table

from openverse_applaunch.objects.base import ServiceConfig, ServiceStatus
from openverse_applaunch.objects.types import HealthCheckDict


class TableManager:
    def __init__(self, service_name: str, console: Console) -> None:
        self.service_name = service_name
        self.console = console

    def create_main_table(self, config: ServiceConfig) -> Table:
        table = Table(
            show_header=True,
            header_style="bold cyan",
            title=f"FastAPI {self.service_name} started",
            title_style="bold magenta",
            border_style="bright_blue",
        )
        table.add_column("Parameter", style="cyan", justify="right")
        table.add_column("Value", style="green")
        # table.add_column("Description", style="yellow")

        if not config:
            raise ValueError("Not configution found")

        for attr_key, attr_value in vars(config).items():
            table.add_row(attr_key, str(attr_value))

        return table

    def create_check_services_table(self, health_dict: HealthCheckDict) -> Table:
        table = Table(
            show_header=True,
            header_style="bold red",
            title="HealthCheck Services",
            title_style="bold magenta",
            border_style="bright_blue",
        )

        table.add_column("Service", style="purple", justify="center")
        table.add_column("Status", style="white", justify="center")
        table.add_column("Detail", style="white", justify="center")
        table.add_column("Additional Info", style="white", justify="center")

        for service_name, health_result in health_dict.items():
            status_style = {
                ServiceStatus.HEALTHY: "green",
                ServiceStatus.UNHEALTHY: "red",
                ServiceStatus.UNKNOWN: "yellow",
            }.get(health_result.status, "white")

            details_str = (
                "\n".join(f"{k}: {v}" for k, v in health_result.details.items())
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
