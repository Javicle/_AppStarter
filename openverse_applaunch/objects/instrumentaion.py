from fastapi import FastAPI
from sqlalchemy.engine import Engine

from openverse_applaunch.objects.exceptions import OpenTelemetryError


def fastapi_instrumentation(app: FastAPI) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import (  # type: ignore
            FastAPIInstrumentor,
        )
    except ImportError:
        raise OpenTelemetryError("FastApi instrumentation is not installed")

    FastAPIInstrumentor.instrument_app(app)  # type: ignore


def sqlalchemy_instrumentation(engine: Engine) -> None:
    if engine:
        try:
            from opentelemetry.instrumentation.sqlalchemy import (  # type: ignore
                SQLAlchemyInstrumentor,
            )
        except ImportError:
            raise OpenTelemetryError("SQLAlchemy instrumentation is not installed")

        SQLAlchemyInstrumentor().instrument(engine=engine)

