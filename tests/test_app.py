import pytest
from fastapi.testclient import TestClient
from lab_api import app


@pytest.fixture
def test_client():
    client = TestClient(app)
    yield client


def test_lab_status(test_client):
    response = test_client.get("/status")
    assert b"default" in response.status


def test_lab_reset(test_client):
    response = test_client.put("/reset")
    assert b"complete" in response.status
