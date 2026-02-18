import pytest

from app import app as flask_app


def test_index_returns_200():
    client = flask_app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
