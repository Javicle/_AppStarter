import asyncio

from openverse_applaunch.objects.base import AbstractTracerService
from openverse_applaunch.objects.types import TracersType


class TracerManager:
    def __init__(self) -> None:
        self.tracers: TracersType = {}

    async def initialize_tracers(self) -> None:
        await asyncio.gather(
            *(asyncio.create_task(tracer.init()) for tracer in self.tracers.values())
        )

    def add_tracer(self, service_name: str, tracer: AbstractTracerService) -> None:
        if service_name in self.tracers or tracer in self.tracers.values():
            raise ValueError(f"Tracer with name '{service_name}' or '{tracer}' already exists")
        self.tracers[service_name] = tracer

    def remove_tracer(self, service_name: str) -> None:
        if service_name not in self.tracers:
            raise ValueError(f"Tracer with name '{service_name}' does not exist")
        del self.tracers[service_name]

    def get_tracer(self, service_name: str) -> AbstractTracerService:
        if service_name not in self.tracers:
            raise ValueError(f"Tracer with name '{service_name}' does not exist")
        return self.tracers[service_name]
