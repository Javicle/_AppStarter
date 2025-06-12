"""
Implementation of telemetry and tracing services.
"""

import logging
import time
from typing import Any

import httpx
from fastapi import status
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from openverse_applaunch.objects.abc import AbstractTracerService
from openverse_applaunch.objects.models.health import (
    HealthCheckResult,
    HealthyResult,
    UnhealthyResult,
    UnknownResult,
)
from openverse_applaunch.objects.types import Sentinal

# Configure logger
logger = logging.getLogger(__name__)


class JaegerService(AbstractTracerService[HealthCheckResult]):
    """
    Jaeger-based tracing service.

    Provides integration with the Jaeger distributed tracing system
    through the OpenTelemetry protocol.
    """

    def __init__(self) -> None:
        """
        Initialize the Jaeger service.

        Sets up the service name and initialization state.
        """
        self.service_name = "jaeger"
        self._initialized: bool = False
        logger.info(
            f"JaegerService instance created with service name: {self.service_name}"
        )

    async def init(self, service_name: str, endpoint: str | None = Sentinal) -> None:
        """
        Initialize the tracer provider and exporter for Jaeger.

        Args:
            service_name: Service name for tracing
            endpoint: Jaeger endpoint URL, defaults to http://localhost:4318/v1/traces

        Raises:
            Exception: If initialization fails
        """
        try:
            logger.info(f"Initializing Jaeger service for service: {service_name}")

            # Set up resource with service name
            resource = Resource(attributes={SERVICE_NAME: service_name})
            logger.debug(f"Created resource with service name: {service_name}")

            # Create and set tracer provider
            trace_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(trace_provider)
            logger.debug("Tracer provider created and set")

            # Determine endpoint URL
            jaeger_endpoint = (
                "http://localhost:4318/v1/traces" if endpoint is Sentinal else endpoint
            )
            logger.info(f"Using Jaeger endpoint: {jaeger_endpoint}")

            # Set up OTLP exporter
            otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace_provider.add_span_processor(span_processor)
            logger.debug("OTLP exporter and span processor configured")

            # Set up console exporter for debugging
            console_exporter = ConsoleSpanExporter()
            trace_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.debug("Console exporter configured")

            self._initialized = True
            logger.info(f"Jaeger service successfully initialized for: {service_name}")

        except Exception as exc:
            logger.error(f"Failed to initialize Jaeger service: {exc}", exc_info=True)
            self._initialized = False
            raise

    async def clean(self, *args: Any, **kwargs: Any) -> None:
        """
        Clean up tracing service resources.

        Args:
            *args: Variable positional arguments (unused)
            **kwargs: Variable keyword arguments (unused)
        """
        logger.info("Cleaning up Jaeger service resources")

        try:
            self._initialized = False
            logger.debug("Marked service as not initialized")

            provider = trace.get_tracer_provider()
            logger.debug("Retrieved tracer provider for cleanup")

            shutdown_method = getattr(provider, "shutdown", None)
            if callable(shutdown_method):
                shutdown_method()
                logger.info("Tracer provider shutdown completed")
            else:
                logger.warning("Tracer provider does not have a shutdown method")

        except Exception as exc:
            logger.error(f"Error during Jaeger service cleanup: {exc}", exc_info=True)

    async def health_check(self) -> HealthCheckResult:
        """
        Check Jaeger API availability.

        Returns:
            HealthCheckResult: Health check result containing service status and metrics

        Raises:
            ValueError: If the service is not initialized
        """
        logger.debug(f"Performing health check for {self.service_name}")

        if not self._initialized:
            error_msg = f"Service {self.service_name} is not initialized"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            logger.debug("Starting HTTP request to Jaeger health endpoint")
            async with httpx.AsyncClient() as client:
                start_time = time.perf_counter()
                response = await client.get("http://localhost:16686/api/health")
                response_time = time.perf_counter() - start_time

                logger.debug(
                    f"Health check response received in {
                        response_time:.3f
                    }s, status: {response.status_code}"
                )

                if response.status_code == status.HTTP_200_OK:
                    logger.info(
                        f"Health check passed for {
                            self.service_name
                        } (response time: {response_time:.3f}s)"
                    )
                    return HealthyResult(
                        service_name=self.service_name,
                        response_time=response_time,
                    )
                else:
                    logger.warning(
                        f"Health check failed for {
                            self.service_name
                        }: status {response.status_code}"
                    )
                    try:
                        response_details = response.json()
                    except Exception as json_error:
                        logger.debug(f"Failed to parse response JSON: {json_error}")
                        response_details = {"error": "Failed to parse response"}

                    return UnhealthyResult(
                        service_name=self.service_name,
                        details=response_details,
                        response_time=response_time,
                    )

        except httpx.RequestError as exc:
            logger.error(
                f"HTTP request error during health check for {self.service_name}: {exc}"
            )
            return UnknownResult(
                service_name=self.service_name,
                message=str(exc),
            )
        except Exception as exc:
            logger.error(
                f"Unexpected error during health check for {self.service_name}: {exc}",
                exc_info=True,
            )
            return UnknownResult(
                service_name=self.service_name,
                message=f"Unexpected error: {str(exc)}",
            )
