from flask import Flask
from genie.testbed import load

from .services import DeviceLab


app = Flask(__name__)

# Default response template
def gen_resp(
    dnac: str = None,
    ise: str = None,
    vmanage: str = None,
    devices: dict = None,
    reset=None,
) -> dict:
    resp = {
        "status": {
            "dnac": dnac,
            "ise": ise,
            "vmanage": vmanage,
        }
    }
    resp["status"].update(devices)
    if reset:
        resp.update({"reset": reset})
    return resp

# If we're using pyATS Lib, we will load the testbed that is a model of the lab.
def get_testbed():
    return load("lab_data/testbed.yaml")

# Get status of lab, e.g. default or configured.
@app.get("/status")
def status():
    # device_lab = DeviceLab(get_testbed())
    # status = device_lab.get_device_status()
    devices = {"dev1": "default", "dev2": "default"}
    return gen_resp("default", "default", "default", devices)

# Reset the state of the entire lab back to default.
@app.put("/reset")
def reset():
    devices = {"dev1": "default", "dev2": "default"}
    return gen_resp("default", "default", "default", devices, "complete")

@app.get("/example")
def example():
    lab = DeviceLab(get_testbed())
    lab.connect_to_all()
    lab.update_default_cfg_exists()
    return lab.get_default_cfg_exists()