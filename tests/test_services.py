import pytest
from genie.testbed import load
from lab_api import services


@pytest.fixture()
def testbed():
    # Setup testbed for testing
    testbed = load("lab_data/testbed.yaml")
    yield testbed


def test_devicelab_testbed(testbed):
    lab = services.DeviceLab(testbed)
    assert testbed == lab.testbed
