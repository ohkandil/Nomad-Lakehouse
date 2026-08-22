"""Tests for dashboard login routes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from dashboard.app import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_login_with_valid_credentials_redirects(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_login_with_invalid_credentials_redirects_back(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"].startswith("/login")


def test_login_page_renders(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == 200
    assert "login-form" in response.text


def test_root_redirects_to_login_when_unauthenticated(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    # RedirectResponse defaults to 307 when no explicit status is set
    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/login"


def test_root_renders_overview_after_login(client: TestClient) -> None:
    client.post("/login", data={"username": "admin", "password": "admin"})
    response = client.get("/")
    assert response.status_code == 200
    assert "overall-status-value" in response.text
