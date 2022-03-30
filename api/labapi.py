from flask import Flask

lab = Flask(__name__)


@lab.route("/status", methods=["GET"])
def status():
    resp = {
        "status": {
            "dnac": "default",
            "ise": "default",
            "vmanage": "default",
        },
    }
    return resp


@lab.route("/reset", methods=["PUT"])
def reset():
    resp = {
        "reset": "complete",
        "status": {
            "dnac": "default",
            "ise": "default",
            "vmanage": "default",
        },
    }
    return resp
