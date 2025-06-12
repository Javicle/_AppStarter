# noqa: WPS601
from dataclasses import dataclass
from typing import Any, AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from rich.console import Console
from rich.table import Table

from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.abc.interfaces import (
    ITableCreator,
    ITableRender,
    TableConfigProtocol,
)
from openverse_applaunch.objects.abc.service import AbstractTracerService
from openverse_applaunch.objects.containers import Container
from openverse_applaunch.objects.managers.health import HealthManager
from openverse_applaunch.objects.managers.lifecycle import LifeCycleManager
from openverse_applaunch.objects.managers.metrics import MetricsManager
from openverse_applaunch.objects.managers.table import TableManager
from openverse_applaunch.objects.managers.table.core import UtilsManager
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.managers.tracer import TracerManager
from openverse_applaunch.objects.models.health import HealthCheckResult, HealthyResult
from tests.constants import TEST_SERVICE_NAME


class MockTableCreator(ITableCreator):
    def __init__(self):
        self.called_with_config = None

    def create_table(self, table_config: TableConfigProtocol) -> Table:
        self.called_with_config = table_config
        mock_table = Table(
            title="Mock Table",
            show_header=True,
            title_style="bold red",
            border_style="blue",
            header_style="italic",
        )
        mock_table.add_column("Mock Column 1")
        mock_table.add_column("Mock Column 2")
        return mock_table


@dataclass
class MockTableConfig(TableConfigProtocol):
    title: str = "Test Title"
    title_style: str = "bold"
    show_header: bool = True
    header_style: str = "underline"
    show_border: bool = True
    border_style: str = "green"
    padding: int = 1
    expand: bool = False


class MockTableRender(ITableRender):
    def __init__(self):
        self.last_populate_args = None
        self.last_populate_kwargs = None

    def populate_table(self, table: Table, *args: Any, **kwargs: Any) -> Table:
        self.last_populate_args = args
        self.last_populate_kwargs = kwargs
        table.add_row("mock_key", "mock_value")
        return table


@pytest.fixture
def test_config() -> dict[str, Any]:
    return {
        "service_name": "test",
        "version": 0.1,
    }


@pytest.fixture
def mock_render() -> MockTableRender:
    return MockTableRender()


@pytest.fixture
def mock_creator() -> MockTableCreator:
    return MockTableCreator()


@pytest.fixture
def mock_config() -> MockTableConfig:
    return MockTableConfig()


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
            message="Most tracer is healthy",
            response_time=0
        )


@pytest.fixture(autouse=False)
def container() -> Container:
    _container = Container()
    _container.config.from_dict(
        {
            "service_name": TEST_SERVICE_NAME,
            "environment": "testing",
            "host": "localhost",
            "port": "8000",
        }
    )
    _container.wire(modules=["openverse_applaunch.main", "tests.test_application",
                             "openverse_applaunch.objects.managers.table.registry"])

    _container.utils_manager.override(UtilsManager())
    _container.storage.override(StorageVars())
    _container.console.override(Console(record=True))  # type: ignore
    _container.metrics_manager.override(
        MetricsManager(console=_container.console())
    )  # type: ignore
    _container.tracer_manager.override(TracerManager())  # type: ignore
    _container.health_manager.override(HealthManager())  # type: ignore
    _container.table_manager.override(  # type: ignore
        TableManager(
            console=_container.console(),
            utils_manager=_container.utils_manager()
        )
    )
    _container.lifecycle_manager.override(  # type: ignore
        LifeCycleManager(service_name=TEST_SERVICE_NAME)
    )
    return _container


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
