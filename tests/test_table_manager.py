"""
This module needs to test table_manager which is realized rich library
"""

import asyncio

from tools_openverse import settings

from openverse_applaunch import ApplicationManager, JaegerService
from tests.conftest import MockTableConfig, MockTableCreator, MockTableRender
from tests.constants import TEST_SERVICE_NAME

mock_render = MockTableRender()
mock_creator = MockTableCreator()
mock_config = MockTableConfig()


async def test_table(mock_render: MockTableRender, mock_creator: MockTableCreator,
                     mock_config: MockTableConfig) -> None:
    app = ApplicationManager.create(TEST_SERVICE_NAME)
    jaeger = JaegerService()

    await jaeger.init(service_name=TEST_SERVICE_NAME)
    app.add_service(service=jaeger)

    await app.initialize_application(
        config=settings.to_dict(),
        with_metrics=False,
        with_tracers=False,
        health_check=True,
    )


if __name__ == "__main__":
    asyncio.run(test_table(mock_render, mock_creator, mock_config))
