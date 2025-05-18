# noqa: WPS601
from typing import Any, AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from rich.console import Console

from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.abc.service import AbstractTracerService
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.enum import ServiceStatus
from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.metrics import MetricsManager
from openverse_applaunch.objects.managers.table import TableManager
from openverse_applaunch.objects.managers.table.core import UtilsManager
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.managers.tracer import TracerManager
from openverse_applaunch.objects.models.health import HealthCheckResult, HealthyResult
from tests.constants import TEST_SERVICE_NAME


@pytest.fixture
def test_config() -> dict[str, Any]:
    return {
        "service_name": "test",
        "version": 0.1,
    }


class MockTestService(AbstractTracerService[HealthCheckResult]):
    service_name: str = "test_service_mock"
    _initialized: bool = False

    async def init(self, *args: Any, **kwargs: Any) -> None:
        self._initialized = True

    async def clean(self, *args: Any, **kwargs: Any) -> None:
        self._initialized = False

    async def health_check(self, *args: Any, **kwargs: Any) -> HealthCheckResult:
        return HealthyResult(
            service_name="test",
            status=ServiceStatus.HEALTHY,
            message="Most tracer is healthy",
            response_time=0.0,
        )


@pytest.fixture(autouse=True)
def container() -> Container:
    container_ = Container()
    container_.config.from_dict(
        {
            "service_name": TEST_SERVICE_NAME,
            "environment": "testing",
            "host": "localhost",
            "port": "8000",
        }
    )
    container_.wire(modules=["openverse_applaunch.main", "tests.test_application",
                             "openverse_applaunch.objects.managers.table.registry"])

    container_.utils_manager.override(UtilsManager())
    container_.storage.override(StorageVars())
    container_.console.override(Console(record=True))  # type: ignore
    container_.metrics_manager.override(
        MetricsManager(console=container_.console())
    )  # type: ignore
    container_.tracer_manager.override(TracerManager())  # type: ignore
    container_.health_manager.override(HealthManager())  # type: ignore
    container_.table_manager.override(  # type: ignore
        TableManager(
            service_name=TEST_SERVICE_NAME,
            console=container_.console(),
            utils_manager=container_.utils_manager()
        )
    )
    container_.lifecycle_manager.override(  # type: ignore
        LifeCycleManager(service_name=TEST_SERVICE_NAME)
    )
    return container_


@pytest.fixture
def get_storage() -> StorageVars:
    return StorageVars()


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
