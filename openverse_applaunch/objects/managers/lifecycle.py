"""
Application lifecycle manager.
"""
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Callable, Optional
from fastapi import FastAPI
from openverse_applaunch.objects.types import Sentinal


class LifeCycleManager:
    """
    FastAPI application lifecycle manager.
    Responsible for creating FastAPI applications and managing their lifecycle.

    Attributes:
        service_name (str): Name of the service.
        lifespan (Optional[Callable]): FastAPI application lifecycle function.
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
        if self.lifespan is not Sentinal:
            return FastAPI(lifespan=self.lifespan)

        @asynccontextmanager
        async def default_lifespan(app: FastAPI) -> AsyncIterator[None]:
            yield

        return FastAPI(lifespan=default_lifespan, title=self.service_name)
