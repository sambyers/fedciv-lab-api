import pytest
from lab_api import app


@pytest.fixture()
def app_setup():
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app_setup):
    return app_setup.test_client()


def test_lab_status(client):
    response = client.get("/status")
    assert b"default" in response.data


def test_lab_reset(client):
    response = client.put("/reset")
    assert b"complete" in response.data
