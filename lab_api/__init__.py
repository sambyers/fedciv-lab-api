from flask import Flask
from genie.testbed import load

# from lab_models import Lab


app = Flask(__name__)


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


def get_testbed():
    return load("lab_data/testbed.yaml")


@app.route("/status", methods=["GET"])
def status():
    # lab = Lab(get_testbed())
    # status = lab.get_device_status()
    devices = {"dev1": "default", "dev2": "default"}
    return gen_resp("default", "default", "default", devices)


@app.route("/reset", methods=["PUT"])
def reset():
    devices = {"dev1": "default", "dev2": "default"}
    return gen_resp("default", "default", "default", devices, "complete")
