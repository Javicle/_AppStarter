from typing import TypeAlias

from openverse_applaunch.objects.base import AbstractTracerService, HealthCheckResult

TracersType: TypeAlias = dict[str, AbstractTracerService]
HealthCheckDict: TypeAlias = dict[str, HealthCheckResult]
NullDict: TypeAlias = dict[None, None]
