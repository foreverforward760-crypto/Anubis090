import os
os.environ["ANUBIS_API_KEY"] = "a" * 40
os.environ["ANUBIS_DEMO_KEY"] = "b" * 40
os.environ["ANUBIS_CORS_ORIGINS"] = "https://example.test"
os.environ["ANUBIS_DB_PATH"] = ":memory:"

import pytest
from fastapi import HTTPException
from starlette.routing import Mount

import app as anubis


def test_missing_api_key_is_rejected():
    with pytest.raises(HTTPException) as exc:
        anubis.verify_api_key(None)
    assert exc.value.status_code == 401


def test_unconfigured_master_key_disables_authenticated_endpoints(monkeypatch):
    monkeypatch.setattr(anubis, "API_KEY", None)
    with pytest.raises(HTTPException) as exc:
        anubis.verify_api_key("x" * 40)
    assert exc.value.status_code == 503


def test_short_demo_key_is_rejected(monkeypatch):
    monkeypatch.setattr(anubis, "DEMO_KEY", "weak")
    with pytest.raises(HTTPException) as exc:
        anubis.verify_api_key("a" * 40)
    assert exc.value.status_code == 503


def test_cors_uses_explicit_origin_allowlist():
    assert anubis.CORS_ORIGINS == ["https://example.test"]
    assert "*" not in anubis.CORS_ORIGINS


def test_api_routes_are_registered_before_root_static_mount():
    api_index = next(
        i for i, route in enumerate(anubis.app.routes)
        if getattr(route, "path", None) == "/api/classify"
    )
    root_mount_index = next(
        i for i, route in enumerate(anubis.app.routes)
        if isinstance(route, Mount) and route.path == "/"
    )
    assert api_index < root_mount_index
