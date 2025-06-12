"""
Registry decorators for table creators, renderers, and configurations.

This module provides decorators to automatically register table-related classes
with the application container upon instantiation.
"""

from typing import Callable, Optional, TypeVar, overload

from tools_openverse import setup_logger

from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    ITableRender,
    TableConfigProtocol,
)
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.types import Sentinal

# Configure logging
logger = setup_logger(__name__)

# Type variables for generic type hints
TCFG = TypeVar("TCFG", bound=TableConfigProtocol)
TC = TypeVar("TC", bound=ITableCreator)
TR = TypeVar("TR", bound=ITableRender)


@overload
def register_table_creator(table_name: str) -> Callable[[type[TC]], type[TC]]: ...


@overload
def register_table_creator(table_name: str, table_creator: TC) -> None: ...


@overload
def register_table_render(table_name: str) -> Callable[[type[TR]], type[TR]]: ...


@overload
def register_table_render(table_name: str, table_renderer: TR) -> None: ...


@overload
def register_table_config(table_name: str) -> Callable[[type[TCFG]], type[TCFG]]: ...


@overload
def register_table_config(table_name: str, table_config: TCFG) -> None: ...


def register_table_creator(
    table_name: str, table_creator: Optional[TC] = Sentinal
) -> Callable[[type[TC]], type[TC]] | None:
    """
    Decorator to register table creator classes with the container.

    If used without passing a class, returns a decorator that instantiates
    and registers the class under the given `table_name`. If a `table_creator`
    instance is provided directly, registers it immediately.
    """
    logger.debug(f"Creating table creator decorator for: '{table_name}'")

    if table_creator is Sentinal:
        def wrapper(cls: type[TC]) -> type[TC]:
            logger.info(
                f"Registering table creator class '{cls.__name__}' as '{table_name}'"
            )

            try:
                logger.debug("Instantiating table creator via decorator")
                instance = cls()
                Container.utils_manager().add(name=table_name, table_obj=instance)
                logger.info(f"Successfully registered table creator '{table_name}'")
                return cls

            except Exception as exc:
                logger.error(f"Failed to register table creator '{table_name}': {exc}")
                raise

        return wrapper

    else:
        if table_creator:
            try:
                logger.debug("Registering provided table creator instance")
                Container.utils_manager().add(name=table_name, table_obj=table_creator)
                logger.info(f"Successfully registered table creator '{table_name}'")
            except Exception as exc:
                logger.error(f"Failed to register table creator '{table_name}': {exc}")
                raise
        else:
            logger.error(
                "Cannot register table creator: provided instance is None (%s)",
                table_name
            )
            raise ValueError(
                f"table_creator cannot be None when registering '{table_name}'"
            )

        return None


def register_table_render(
    table_name: str, table_renderer: Optional[TR] = Sentinal
) -> Callable[[type[TR]], type[TR]] | None:
    """
    Decorator to register table renderer classes with the container.

    If used without passing a class, returns a decorator that instantiates
    and registers the class under the given `table_name`. If a `table_renderer`
    instance is provided directly, registers it immediately.
    """
    logger.debug(f"Creating table render decorator for: '{table_name}'")

    if table_renderer is Sentinal:
        def wrapper(cls: type[TR]) -> type[TR]:
            logger.info(
                f"Registering table renderer class '{cls.__name__}' as '{table_name}'"
            )

            try:
                logger.debug("Instantiating table renderer via decorator")
                instance = cls()
                Container.utils_manager().add(name=table_name, table_obj=instance)
                logger.info(f"Successfully registered table renderer '{table_name}'")
                return cls

            except Exception as exc:
                logger.error(f"Failed to register table renderer '{table_name}': {exc}")
                raise

        return wrapper

    else:
        if table_renderer:
            try:
                logger.debug("Registering provided table renderer instance")
                Container.utils_manager().add(name=table_name, table_obj=table_renderer)
                logger.info(f"Successfully registered table renderer '{table_name}'")
            except Exception as exc:
                logger.error(f"Failed to register table renderer '{table_name}': {exc}")
                raise
        else:
            logger.error(
                "Cannot register table renderer: provided instance is None (%s)",
                table_name
            )
            raise ValueError(
                f"table_renderer cannot be None when registering '{table_name}'"
            )

        return None


def register_table_config(
    table_name: str, table_config: Optional[TCFG] = Sentinal
) -> Callable[[type[TCFG]], type[TCFG]] | None:
    """
    Decorator to register table configuration classes with the container.

    If used without passing a class, returns a decorator that instantiates
    and registers the class under the given `table_name`. If a `table_config`
    instance is provided directly, registers it immediately.
    """
    logger.debug(f"Creating table config decorator for: '{table_name}'")

    if table_config is Sentinal:
        def wrapper(cls: type[TCFG]) -> type[TCFG]:
            logger.info(
                f"Registering table config class '{cls.__name__}' as '{table_name}'"
            )

            try:
                logger.debug("Instantiating table config via decorator")
                instance = cls()
                Container.utils_manager().add(name=table_name, table_obj=instance)
                logger.info(f"Successfully registered table config '{table_name}'")
                return cls

            except Exception as exc:
                logger.error(f"Failed to register table config '{table_name}': {exc}")
                raise

        return wrapper

    else:
        if table_config:
            try:
                logger.debug("Registering provided table config instance")
                Container.utils_manager().add(name=table_name, table_obj=table_config)
                logger.info(f"Successfully registered table config '{table_name}'")
            except Exception as exc:
                logger.error(f"Failed to register table config '{table_name}': {exc}")
                raise
        else:
            logger.error(
                "Cannot register table config: provided instance is None (%s)",
                table_name
            )
            raise ValueError(
                f"table_config cannot be None when registering '{table_name}'"
            )

        return None
