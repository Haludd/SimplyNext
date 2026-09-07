from __future__ import annotations

import pytest
from pydantic import ValidationError

from simplynext.config import Settings


def test_railway_port_overrides_local_prefixed_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLYNEXT_PORT", "8123")
    monkeypatch.delenv("PORT", raising=False)
    assert Settings(_env_file=None).port == 8123

    monkeypatch.setenv("PORT", "9123")
    assert Settings(_env_file=None).port == 9123


@pytest.mark.parametrize("value", ["0", "65536", "not-a-port"])
def test_railway_port_obeys_existing_safe_range(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PORT", value)
    with pytest.raises(ValidationError, match="(?i)port"):
        Settings(_env_file=None)
