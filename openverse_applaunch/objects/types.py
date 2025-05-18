"""
Common types for project
"""


from typing import Any, TypeVar

from openverse_applaunch.objects.abc.heath import HealthResultProtocolType
from openverse_applaunch.objects.abc.service import SomeAbstractServiceType

THeatlhResult = TypeVar('THeatlhResult', bound="HealthResultProtocolType")
TService = TypeVar("TService", bound=SomeAbstractServiceType)

TSorH = TypeVar('TSorH', bound=HealthResultProtocolType | SomeAbstractServiceType)

Sentinal: Any = object()

