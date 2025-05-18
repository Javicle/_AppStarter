from enum import Enum


class Color(Enum):
    """Enum class for colors"""
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    BLACK = "black"
    PURPLE = 'purple'


class Style(Enum):
    """Enum class for styles"""
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"


class TableType(Enum):
    MAIN = 'main'
    SERVICE = 'service'


class ServiceStatus(Enum):
    """Services status enum class"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
