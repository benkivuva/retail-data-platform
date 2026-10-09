"""Tests for the authentication layer."""
from __future__ import annotations


def test_health_is_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_dashboard_redirects_when_logged_out(client):
    resp = client.get("/dashboards/operations/")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_login_with_wrong_password_fails(client):
    resp = client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


def test_login_succeeds_with_valid_credentials(client):
    resp = client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "testpass"},
        follow_redirects=False,
    )
    assert resp.status_code == 302


def test_logout_redirects_to_login(client):
    client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "testpass"},
    )
    resp = client.get("/auth/logout")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]