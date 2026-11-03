import os
import time
import logging

from flask import Flask, g, request
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_opentelemetry(app: Flask):
    resource = Resource.create({
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "attijari-backend-api")
    })

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "https://otlp-gateway-prod-us-east-0.grafana.net/otlp",
    )
    headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers_dict = {}
    for header in headers_raw.split(","):
        if "=" in header:
            key, value = header.split("=", 1)
            headers_dict[key.strip()] = value.strip()

    def signal_endpoint(signal: str) -> str:
        base_endpoint = endpoint.rstrip("/")
        for existing_signal in ("traces", "logs", "metrics"):
            suffix = f"/v1/{existing_signal}"
            if base_endpoint.endswith(suffix):
                base_endpoint = base_endpoint[:-len(suffix)]
                break
        return f"{base_endpoint}/v1/{signal}"

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=signal_endpoint("traces"),
                headers=headers_dict,
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=signal_endpoint("logs"),
                headers=headers_dict,
            )
        )
    )
    _logs.set_logger_provider(logger_provider)
    logging.getLogger().addHandler(
        LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    )
    LoggingInstrumentor().instrument(set_logging_format=False)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=signal_endpoint("metrics"),
            headers=headers_dict,
        )
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter("attijari.backend")
    request_count = meter.create_counter(
        "http.server.request.count",
        unit="1",
        description="Number of HTTP requests handled by the backend.",
    )
    request_duration = meter.create_histogram(
        "http.server.request.duration",
        unit="ms",
        description="Duration of HTTP requests handled by the backend.",
    )

    @app.before_request
    def start_request_timer():
        g.otel_request_start = time.perf_counter()

    @app.after_request
    def record_request_metrics(response):
        route = request.url_rule.rule if request.url_rule else "unmatched"
        attributes = {
            "http.request.method": request.method,
            "http.route": route,
            "http.response.status_code": response.status_code,
        }
        request_count.add(1, attributes)
        request_duration.record(
            (time.perf_counter() - g.otel_request_start) * 1000,
            attributes,
        )
        return response

    FlaskInstrumentor().instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RequestsInstrumentor().instrument()