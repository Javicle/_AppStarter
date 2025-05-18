from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.exceptions import ServiceNotFoundError
from openverse_applaunch.objects.managers.table.storage import StorageVars
from openverse_applaunch.objects.models.config import (
    ModernTableConfig,
    ReportTableConfig,
)
from tests.conftest import MockTestService
from tests.constants import ACCESS_STATUS_RESPONSE, TEST_SERVICE_NAME


@pytest.mark.asyncio
async def test_create_application() -> None:
    """Проверяет базовое создание приложения"""
    app_manager = ApplicationManager(service_name=TEST_SERVICE_NAME)
    assert app_manager.service_name == TEST_SERVICE_NAME
    assert app_manager.app is None  # До инициализации app должен быть None


@pytest.mark.asyncio
async def test_init_application(test_config: dict[str, Any]) -> None:
    """Проверяет инициализацию приложения"""
    app_manager = ApplicationManager(service_name=TEST_SERVICE_NAME)
    await app_manager.initialize_application(
        with_tracers=False, with_metrics=False,
        config=test_config, health_check=False,
    )

    assert isinstance(app_manager.get_app, FastAPI)  # Проверяем, что приложение создано

    # Проверяем, что все менеджеры инициализированы
    assert app_manager._tracer_manager is not None
    assert app_manager._health_manager is not None
    assert app_manager._table_manager is not None


@pytest.mark.asyncio
async def test_endpoint(test_config: dict[str, Any]) -> None:
    """Проверяет создание и работу простого эндпоинта"""
    app_manager = ApplicationManager(service_name=TEST_SERVICE_NAME)
    await app_manager.initialize_application(
        test_config, with_tracers=False, with_metrics=False, health_check=False
    )
    app = app_manager.get_app

    @app.get("/test")
    async def test_route():  # type: ignore
        return {"message": "Hello, Test!"}

    # Используем TestClient для проверки эндпоинта
    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == ACCESS_STATUS_RESPONSE
    assert response.json() == {"message": "Hello, Test!"}


@pytest.mark.asyncio
async def test_health_check(
    mock_test_service: MockTestService, test_config: dict[str, Any],
    get_storage: StorageVars,
) -> None:
    """Проверяет работу проверки здоровья"""
    app_manager = ApplicationManager(service_name="test_service")
    # added service
    app_manager.add_service(mock_test_service)
    # register configs
    app_manager._table_manager.register_service("main", object=ModernTableConfig())
    app_manager._table_manager.register_service("main", object=ReportTableConfig())
    health_status = await app_manager._health_manager.check_services()
    # added vars to storage
    get_storage["health_dict"] = health_status
    get_storage['config'] = test_config
    await app_manager.initialize_application(
        test_config, with_tracers=False, with_metrics=False, health_check=True
    )
    assert get_storage['health_dict']


# Тест создания таблиц
@pytest.mark.asyncio
async def test_table_creation(
    test_config: dict[str, Any],
    get_storage: StorageVars,
    mock_test_service: MockTestService,
) -> None:
    """Проверяет создание информационных таблиц"""
    app_manager = ApplicationManager(service_name="test_service")

    app_manager.add_service(mock_test_service)

    health_dict = await app_manager._health_manager.check_services()
    get_storage['health_dict'] = health_dict
    get_storage['config'] = test_config

    output = app_manager._table_manager.display_tables(storage=get_storage,
                                                       output=True)
    assert output is not None


@pytest.mark.asyncio
async def test_full_workflow(
    mock_test_service: MockTestService, test_config: dict[str, Any]
) -> None:
    """Проверяет полный рабочий процесс"""
    app_manager = ApplicationManager(service_name=TEST_SERVICE_NAME)

    assert not app_manager._tracer_manager.tracers
    assert not app_manager._health_manager.services

    app_manager.add_service(mock_test_service)
    await app_manager.initialize_application(
        test_config, with_tracers=True, with_metrics=False, health_check=True
    )
    app = app_manager.get_app

    @app.get("/status")
    async def status() -> dict[str, str]:  # type: ignore
        return {"status": "operational"}

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == ACCESS_STATUS_RESPONSE
    assert response.json() == {"status": "operational"}

    health_status = await app_manager._health_manager.check_services()
    assert isinstance(health_status, dict)


@pytest.mark.asyncio
async def test_error_handling() -> None:
    """Проверяет обработку ошибок"""
    app_manager = ApplicationManager(service_name=TEST_SERVICE_NAME)

    with pytest.raises(ServiceNotFoundError):
        await app_manager._health_manager.check_service("non_existent_service")


if __name__ == "__main__":
    pytest.main(["-v"])
