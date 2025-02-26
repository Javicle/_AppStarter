from typing import Any, AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from rich.console import Console

from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.base import (
    AbstractTracerService,
    HealthCheckResult,
    ServiceConfig,
    ServiceStatus,
)
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.table import TableManager
from openverse_applaunch.objects.managers.tracer import TracerManager


@pytest.fixture
def test_config() -> ServiceConfig:
    return ServiceConfig(
        service_name="test_service",
        host="localhost",
        port=8000,
        version="1.0.0",
        workers=1,
        debug_mode=True,
        environment="testing",
    )


class MockTestService(AbstractTracerService):
    service_name: str = "test"
    _initialized: bool = False

    async def init(self, *args: Any, **kwargs: Any) -> None:
        self._initialized = True

    async def clean(self, *args: Any, **kwargs: Any) -> None:
        self._initialized = False

    async def health_check(self, *args: Any, **kwargs: Any) -> HealthCheckResult:
        return HealthCheckResult(
            status=ServiceStatus.HEALTHY,
            message="Most tracer is healthy",
            details={"intilized": self._initialized},
        )


@pytest.fixture(autouse=True)
def container() -> Container:
    container_ = Container()
    container_.config.from_dict(
        {
            "service_name": "test_service",
            "environment": "testing",
            "host": "localhost",
            "port": "8000",
        }
    )

    container_.console.override(Console())  # type: ignore
    container_.tracer_manager.override(TracerManager())  # type: ignore
    container_.health_manager.override(HealthManager())  # type: ignore
    container_.table_manager.override(  # type: ignore
        TableManager(service_name="test_service", console=Console())
    )
    container_.lifecycle_manager.override(  # type: ignore
        LifeCycleManager(service_name="test_service")
    )

    container_.wire(modules=["openverse_applaunch.main", "tests.test_application"])

    return container_


@pytest.fixture
def mock_test_service() -> MockTestService:
    return MockTestService()


@pytest.fixture
def test_app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    return TestClient(app=test_app)


@pytest.fixture
async def app_manager() -> AsyncGenerator[ApplicationManager, None]:
    manager = ApplicationManager(service_name="Test")
    yield manager
