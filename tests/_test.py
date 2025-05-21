import pytest

from openverse_applaunch.main import ApplicationManager


@pytest.mark.asyncio
async def test_app() -> None:
    app = ApplicationManager.create(service_name="test")
    await app.initialize_application(config={
        "vers": "0,0,1",
        "Name": "TEST"
    }, with_metrics=False, with_tracers=False, health_check=False)
    
    
@pytest.mark.asyncio
async def test_exception() -> None:
    with pytest.raises(ValueError):
        ApplicationManager(service_name="Agofd")
