"""
Application lifecycle manager with logging.
"""

from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Callable, Optional

from fastapi import FastAPI
from tools_openverse import setup_logger

from openverse_applaunch.objects.types import Sentinal


class LifeCycleManager:
    """
    FastAPI application lifecycle manager.
    Responsible for creating FastAPI applications and managing their lifecycle.

    Attributes:
        service_name (str): Name of the service.
        lifespan (Optional[Callable]): FastAPI application lifecycle function.
        logger (logging.Logger): Logger instance for this manager.
    """

    def __init__(
        self,
        service_name: str,
        lifespan: Optional[Callable[[FastAPI], AsyncContextManager[None]]] = Sentinal,
    ) -> None:
        """
        Initialize the lifecycle manager.

        Attributes:
            service_name: Name of the service.
            lifespan: FastAPI application lifecycle function.
        """
        self.lifespan = lifespan
        self.service_name = service_name
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info(f"Lifecycle manager initialized for service: {service_name}")
        if lifespan is Sentinal:
            self.logger.debug("Using default lifespan function")

        else:
            self.logger.debug("Custom lifespan function provided")

    def create_application(self) -> FastAPI:
        """
        Create a FastAPI application instance.

        If a lifespan function is provided, it uses that for lifecycle management.
        Otherwise, a default empty context manager is used.

        Returns:
            FastAPI: The created FastAPI application.

        Example:
            ```python
            # Create a lifecycle manager
            lifecycle_manager = LifeCycleManager(service_name="my-service")

            # Create a FastAPI application
            app = lifecycle_manager.create_application()
            ```
        """
        self.logger.debug(
            f"Creating FastAPI application for service: {self.service_name}"
        )

        try:
            if self.lifespan is Sentinal:
                self.logger.debug("Using default lifespan function")

                @asynccontextmanager
                async def default_lifespan(app: FastAPI) -> AsyncIterator[None]:
                    self.logger.info(
                        f"Starting application lifecycle for: {self.service_name}"
                    )
                    try:
                        yield
                    finally:
                        self.logger.info(
                            f"Shutting down application lifecycle for: {
                                self.service_name
                            }"
                        )

                app = FastAPI(lifespan=default_lifespan, title=self.service_name)

            else:
                self.logger.debug("Using custom lifespan function")
                app = FastAPI(lifespan=self.lifespan)

            self.logger.info(
                f"FastAPI application created successfully for: {self.service_name}"
            )
            return app

        except Exception as exc:
            self.logger.error(f"Failed to create FastAPI application: {exc}")
            raise
