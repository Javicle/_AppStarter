import pytest

from openverse_applaunch.objects.containers import Container


@pytest.mark.asyncio
async def test_modules(container: Container) -> None:
    storage = container.storage()
    health_dict = {'health': 123}
    storage['health_dict'] = health_dict

    assert storage['health_dict'] == health_dict


@pytest.mark.asyncio
async def test_check_config() -> None:
    ...