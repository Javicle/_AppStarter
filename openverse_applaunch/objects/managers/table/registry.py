from typing import Any, Callable, TypeVar

from dependency_injector.wiring import Provide, inject

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    ITableRender,
    TableConfigProtocol,
)

from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.managers.table.core import UtilsManager

TCfg = TypeVar("TCfg", bound="TableConfigProtocol")
TC = TypeVar("TC", bound="ITableCreator")
TR = TypeVar("TR", bound="ITableRender")


def register_table_creator(
    table_name: str,
) -> Callable[[type[TC]], type[TC]]:
    def wrapper(cls: type[TC]) -> type[TC]:
        orig_init = cls.__init__
        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            from openverse_applaunch.objects.containers import Container
            Container.utils_manager().add(name=table_name, table_obj=self)
        cls.__init__ = new_init
        return cls
    return wrapper


def register_table_render(
    table_name: str,
) -> Callable[[type[TR]], type[TR]]:
    def wrapper(cls: type[TR]) -> type[TR]:
        orig_init = cls.__init__
        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            from openverse_applaunch.objects.containers import Container
            Container.utils_manager().add(name=table_name, table_obj=self)
        cls.__init__ = new_init
        return cls
    return wrapper


def register_table_config(
    table_name: str,
) -> Callable[[type[TCfg]], type[TCfg]]:
    def wrapper(cls: type[TCfg]) -> type[TCfg]:
        orig_init = cls.__init__
        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            from openverse_applaunch.objects.containers import Container
            Container.utils_manager().add(name=table_name, table_obj=self)
        cls.__init__ = new_init
        return cls
    return wrapper
