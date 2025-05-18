"""
Конкретные реализации сервисов (трассировки, метрики и т.д.).
"""

from openverse_applaunch.objects.services.telemetry import JaegerService

__all__ = [
    "JaegerService",
]
