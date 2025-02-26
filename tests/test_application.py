# tests/test_basic_functionality.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.base import ServiceConfig
from openverse_applaunch.objects.exceptions import ServiceNotFoundError
from tests.conftest import MockTestService


@pytest.mark.asyncio
async def test_create_application() -> None:
    """Проверяет базовое создание приложения"""
    app_manager = ApplicationManager(service_name="test_service")
    assert app_manager.service_name == "test_service"
    assert app_manager.app is None  # До инициализации app должен быть None


@pytest.mark.asyncio
async def test_init_application(test_config: ServiceConfig) -> None:
    """Проверяет инициализацию приложения"""
    app_manager = ApplicationManager(service_name="test_service")
    await app_manager.initialize_application(
        test_config, with_tracers=False, with_health_check=False
    )

    assert isinstance(app_manager.get_app, FastAPI)  # Проверяем, что приложение создано

    # Проверяем, что все менеджеры инициализированы
    assert app_manager.tracer_manager is not None
    assert app_manager.health_manager is not None
    assert app_manager.table_manager is not None


@pytest.mark.asyncio
async def test_endpoint(test_config: ServiceConfig) -> None:
    """Проверяет создание и работу простого эндпоинта"""
    app_manager = ApplicationManager(service_name="test_service")
    await app_manager.initialize_application(
        test_config, with_tracers=False, with_health_check=False
    )
    app = app_manager.get_app

    @app.get("/test")
    async def test_route():  # type: ignore
        return {"message": "Hello, Test!"}

    # Используем TestClient для проверки эндпоинта
    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Test!"}


@pytest.mark.asyncio
async def test_health_check(mock_test_service: MockTestService, test_config: ServiceConfig) -> None:
    """Проверяет работу проверки здоровья"""
    app_manager = ApplicationManager(service_name="test_service")
    app_manager.add_service(mock_test_service)
    await app_manager.initialize_application(
        test_config, with_tracers=False, with_health_check=True
    )

    # Проверяем статус здоровья
    health_status = await app_manager.health_manager.check_services()
    assert isinstance(health_status, dict)


# Тест создания таблиц
def test_table_creation(test_config: ServiceConfig) -> None:
    """Проверяет создание информационных таблиц"""
    app_manager = ApplicationManager(service_name="test_service")

    # Проверяем создание основной таблицы
    main_table = app_manager.table_manager.create_main_table(test_config)
    assert main_table is not None
    assert main_table.title == "FastAPI test_service started"


@pytest.mark.asyncio
async def test_full_workflow(
    mock_test_service: MockTestService, test_config: ServiceConfig
) -> None:
    """Проверяет полный рабочий процесс"""
    app_manager = ApplicationManager(service_name="test_service")

    app_manager.add_service(mock_test_service)
    await app_manager.initialize_application(test_config, with_tracers=True, with_health_check=True)
    app = app_manager.get_app

    @app.get("/status")
    async def status() -> dict[str, str]:  # type: ignore
        return {"status": "operational"}

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    assert response.json() == {"status": "operational"}

    health_status = await app_manager.health_manager.check_services()
    assert isinstance(health_status, dict)


@pytest.mark.asyncio
async def test_error_handling() -> None:
    """Проверяет обработку ошибок"""
    app_manager = ApplicationManager(service_name="test_service")

    with pytest.raises(ServiceNotFoundError):
        await app_manager.health_manager.check_service("non_existent_service")


if __name__ == "__main__":
    pytest.main(["-v"])
