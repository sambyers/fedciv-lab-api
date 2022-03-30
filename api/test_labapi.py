import pytest
from labapi import lab


@pytest.fixture()
def app():
    lab.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield lab

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


def test_lab_status(client):
    response = client.get("/status")
    assert b"default" in response.data


def test_lab_reset(client):
    response = client.put("/reset")
    assert b"complete" in response.data
