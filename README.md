# OpenVerse AppLaunch

Библиотека для облегчения запуска и мониторинга FastAPI приложений с поддержкой телеметрии, проверок здоровья и метрик.

## Возможности

- 🚀 Автоматическая настройка FastAPI приложения
- 📊 Интеграция с OpenTelemetry для трассировки
- 🔍 Мониторинг здоровья сервисов
- 📈 Сбор и экспорт метрик
- 🎨 Красивый форматированный вывод в консоль с помощью Rich

## Установка

```bash
# Базовая установка
pip install openverse-applaunch

# С поддержкой трассировки
pip install openverse-applaunch[telemetry]

# С поддержкой SQL
pip install openverse-applaunch[sql]

# Все опциональные зависимости
pip install openverse-applaunch[all]

# Для разработки
pip install openverse-applaunch[dev]
```

## Быстрый старт

```python
import asyncio
from fastapi import FastAPI
from openverse_applaunch import ApplicationManager
from openverse_applaunch.objects.base import ServiceConfig, JaegerService

async def main():
    # Создание конфигурации
    config = ServiceConfig(
        service_name="my-app",
        host="localhost",
        port=8000,
        version="1.0.0",
        workers=1,
        debug_mode=True,
        environment="development",
    )

    # Создание и настройка приложения
    async with ApplicationManager(service_name="my-app") as app_manager:
        # Добавление Jaeger трассировки
        jaeger = JaegerService()
        app_manager.add_service(jaeger)

        # Инициализация приложения
        await app_manager.initialize_application(
            config=config,
            with_tracers=True,
            with_health_check=True,
            with_metrics=False
        )

        # Получение FastAPI приложения
        app = app_manager.get_app

        # Определение эндпоинтов
        @app.get("/")
        async def read_root():
            return {"Hello": "World"}

        # Запуск приложения
        app_manager.run(host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    asyncio.run(main())
```

## Архитектура

Библиотека построена на основе менеджеров, каждый из которых отвечает за определенный аспект работы приложения:

- **ApplicationManager** - основной класс для управления приложением
- **HealthManager** - менеджер для проверки здоровья сервисов
- **TracerManager** - менеджер для трассировщиков OpenTelemetry
- **MetricsManager** - менеджер для сбора метрик
- **TableManager** - менеджер для вывода информационных таблиц
- **LifeCycleManager** - менеджер жизненного цикла приложения

## Создание собственных сервисов

Вы можете расширить функциональность, создавая собственные сервисы:

```python
from openverse_applaunch.objects.base import AbstractTracerService, HealthCheckResult, ServiceStatus

class MyCustomService(AbstractTracerService):
    service_name = "my-service"
    _initialized = False

    async def init(self, *args, **kwargs):
        # Инициализация сервиса
        self._initialized = True

    async def clean(self, *args, **kwargs):
        # Очистка ресурсов
        self._initialized = False

    async def health_check(self, *args, **kwargs):
        # Проверка здоровья
        return HealthCheckResult(
            service_name=self.service_name,
            status=ServiceStatus.HEALTHY,
            message="Service is healthy",
            details={"initialized": self._initialized}
        )
```

## Лицензия

MIT
