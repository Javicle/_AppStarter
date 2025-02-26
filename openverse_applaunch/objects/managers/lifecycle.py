from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Callable, Optional

from fastapi import FastAPI


class LifeCycleManager:
    def __init__(
        self,
        service_name: str,
        lifespan: Optional[Callable[[FastAPI], AsyncContextManager[None]]] | None = None,
    ) -> None:
        self.lifespan = lifespan
        self.service_name = service_name

    def create_application(self) -> FastAPI:
        if self.lifespan:
            return FastAPI(lifespan=self.lifespan)

        @asynccontextmanager
        async def default_lifespan(app: FastAPI) -> AsyncIterator[None]:
            yield

        return FastAPI(lifespan=default_lifespan)
