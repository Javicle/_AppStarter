"""
Модели конфигурации для приложения.
"""

from dataclasses import dataclass, field
from typing import Optional

from rich.box import ROUNDED, DOUBLE, Box
from openverse_applaunch.objects.abc.interfaces import TableConfigProtocol
from openverse_applaunch.objects.managers.table.registry import register_table_config


@dataclass
class TableConfig(TableConfigProtocol):
    """
    Define base settings for creating Table using the 'rich' library.

    Attributes:
        title (str): The title of the table.
        title_style (str): The style of the table title (e.g., "bold magenta").
        show_header (bool): Whether to show column headers.
        header_style (str): The style of the column headers.
        show_border (bool): Whether to show the table border.
        border_style (str): The style of the table border (e.g., "dim").
        padding (int): Cell padding (spaces inside cells).
        expand (bool): Whether the table should expand to fill available width.
    """

    title: str
    title_style: str = "bold magenta"
    show_header: bool = True
    header_style: str = "bold cyan"
    show_border: bool = True
    border_style: str = "dim"
    padding: int = 1
    expand: bool = False


@register_table_config('main')
@dataclass
class ModernTableConfig(TableConfig):
    """
    Modern, clean table style with subtle borders and vibrant headers.

    Perfect for dashboards and interactive applications where readability
    and modern aesthetics are important.
    """

    title: str = "Modern Table"
    title_style: str = "bold blue"
    show_header: bool = True
    header_style: str = "bold cyan"
    show_border: bool = True
    border_style: str = "dim blue"
    padding: int = 2
    expand: bool = True
    # Others Settings
    row_styles: list[str] = field(default_factory=lambda: ["", "dim"])
    caption: Optional[str] = None
    caption_style: str = "italic dim"
    box1: Box = ROUNDED


@register_table_config('service')
@dataclass
class ReportTableConfig(TableConfig):
    """
    Professional table style suitable for reports and formal documentation.

    Features clear borders, traditional styling, and excellent readability
    for formal business reports and technical documentation.
    """

    title: str = "Report Table"
    title_style: str = "bold green on black"
    show_header: bool = True
    header_style: str = "bold white on dark_green"
    show_border: bool = True
    border_style: str = "green"
    padding: int = 1
    expand: bool = False
    # Others Settings
    row_styles: list[str] = field(default_factory=lambda: ["", "on grey7"])
    footer_style: str = "italic"
    highlight: bool = True
    highlight_style: str = "bold on dark_green"
    box = DOUBLE
