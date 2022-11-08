import pytest
from fastapi.testclient import TestClient
from lab_api import app


@pytest.fixture
def test_client():
    client = TestClient(app)
    yield client


# def test_lab_status(test_client):
#     response = test_client.get("/status")
#     assert (
#         '{"name":"csr1000v-1","status":"configured","ip":"10.0.0.1",'
#         '"credentials":null,"default_cfg":true}' in response.text
#     )


# def test_lab_reset(test_client):
#     response = test_client.put("/reset")
#     assert "default" in response.text
