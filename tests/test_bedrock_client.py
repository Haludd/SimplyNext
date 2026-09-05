from __future__ import annotations

from typing import Any

import boto3

import simplynext.orchestrator as orchestrator
from simplynext.agent import BedrockCaptionAssembler, create_bedrock_client
from simplynext.config import Settings
from simplynext.observability import MetricsRegistry


def test_create_bedrock_client_defaults_are_bounded(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_client(service_name: str, **kwargs: Any) -> object:
        captured["service_name"] = service_name
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(boto3, "client", fake_client)

    create_bedrock_client(region_name="ap-southeast-1")

    client_config = captured["config"]
    assert client_config.connect_timeout == 5.0
    assert client_config.read_timeout == 30.0
    assert client_config.retries == {
        "mode": "standard",
        "total_max_attempts": 3,
    }


def test_create_bedrock_client_applies_explicit_transport_limits(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    expected_client = object()

    def fake_client(service_name: str, **kwargs: Any) -> object:
        captured["service_name"] = service_name
        captured.update(kwargs)
        return expected_client

    monkeypatch.setattr(boto3, "client", fake_client)

    client = create_bedrock_client(
        region_name="ap-southeast-2",
        connect_timeout_seconds=1.25,
        read_timeout_seconds=8.5,
        total_max_attempts=4,
    )

    assert client is expected_client
    assert captured["service_name"] == "bedrock-runtime"
    assert captured["region_name"] == "ap-southeast-2"
    client_config = captured["config"]
    assert client_config.connect_timeout == 1.25
    assert client_config.read_timeout == 8.5
    assert client_config.retries == {
        "mode": "standard",
        "total_max_attempts": 4,
    }


def test_build_translation_engine_forwards_bedrock_transport_limits(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class StubClient:
        def converse(self, **kwargs: Any) -> dict[str, object]:
            raise AssertionError("the client must not be called while building the engine")

    def fake_create_bedrock_client(**kwargs: Any) -> StubClient:
        captured.update(kwargs)
        return StubClient()

    monkeypatch.setattr(orchestrator, "create_bedrock_client", fake_create_bedrock_client)
    settings = Settings(
        _env_file=None,
        bedrock_enabled=True,
        aws_region="us-west-2",
        bedrock_connect_timeout_seconds=2.5,
        bedrock_read_timeout_seconds=25.0,
        bedrock_total_max_attempts=2,
    )

    engine = orchestrator.build_translation_engine(settings, MetricsRegistry())

    assert isinstance(engine.assembler, BedrockCaptionAssembler)
    assert captured == {
        "region_name": "us-west-2",
        "connect_timeout_seconds": 2.5,
        "read_timeout_seconds": 25.0,
        "total_max_attempts": 2,
    }


def test_settings_load_bedrock_transport_limits_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("SIMPLYNEXT_BEDROCK_CONNECT_TIMEOUT_SECONDS", "3.5")
    monkeypatch.setenv("SIMPLYNEXT_BEDROCK_READ_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("SIMPLYNEXT_BEDROCK_TOTAL_MAX_ATTEMPTS", "5")

    settings = Settings(_env_file=None)

    assert settings.bedrock_connect_timeout_seconds == 3.5
    assert settings.bedrock_read_timeout_seconds == 45.0
    assert settings.bedrock_total_max_attempts == 5
