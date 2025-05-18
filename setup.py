from setuptools import find_packages, setup

setup(
    name="openverse-applaunch",
    version="0.1.0",
    description="Application Launcher and Runtime Framework for OpenVerse Project",
    long_description="""
    OpenVerse AppLaunch - библиотека для легкого запуска FastAPI приложений
    с поддержкой трассировки, мониторинга здоровья и метрик.
    Основные возможности:
    * Автоматическая настройка FastAPI приложения
    * Интеграция с OpenTelemetry для трассировки
    * Мониторинг здоровья сервисов
    * Сбор и экспорт метрик
    * Красивый форматированный вывод в консоль
    """,
    long_description_content_type="text/markdown",
    author="Javicle",
    author_email="qubackx@gmail.com",
    url="https://github.com/javicle/openverse-applaunch",
    packages=find_packages(),
    package_data={"openverse_applaunch": ["py.typed"]},
    include_package_data=True,
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
    ],
    install_requires=[
        "fastapi>=0.88.0",
        "setuptools>=65.0.0",
        "rich>=13.0.0",
        "dependency_injector>=4.41.0",
        "uvicorn>=0.20.0",
    ],
    extras_require={
        "telemetry": [
            "opentelemetry-instrumentation-fastapi>=0.36b0",
            "opentelemetry-sdk>=1.15.0",
            "opentelemetry-exporter-otlp-proto-http>=1.15.0",
        ],
        "sql": [
            "sqlalchemy>=2.0.0",
            "opentelemetry-instrumentation-sqlalchemy>=0.36b0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "opentelemetry-instrumentation-fastapi>=0.36b0",
            "opentelemetry-sdk>=1.15.0",
            "opentelemetry-exporter-otlp-proto-http>=1.15.0",
            "sqlalchemy>=2.0.0",
            "opentelemetry-instrumentation-sqlalchemy>=0.36b0",
        ],
    },
)
