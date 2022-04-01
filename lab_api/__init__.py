from fastapi import FastAPI
from pydantic import BaseModel
from genie.testbed import load
from .services import DeviceLab


app = FastAPI()

# Response Models
class Status(BaseModel):
    dnac: dict | None = None
    sdwan: dict | None = None
    ise: dict | None = None
    devices: list[dict] | None = None

class Response(BaseModel):
    status: Status | None = None

# Response templates
response = {
    'status': {
        'dnac': None,
        'sdwan': None,
        'ise': None,
        'devices': None,
    },
}

# name is the system's name, status is default or configured
component_resp = {'name': None, 'status': None}

# If we're using pyATS Lib, we will load the testbed that is a model of the lab.
def get_testbed():
    return load("lab_data/testbed.yaml")


# Get status of lab, e.g. default or configured.
@app.get("/status", response_model=Response)
def status():
    # device_lab = DeviceLab(get_testbed())
    # status = device_lab.get_device_status()
    
    # Fake dnac info that would come from a backing service
    dnac_resp = component_resp.copy()
    dnac_resp['name'] = 'dnac1'
    dnac_resp['status'] = 'default'
    response['status']['dnac'] = dnac_resp
    response['status']['devices'] = []
    # Fill out some fake devices
    for i in range(5):
        device = component_resp.copy()
        device['name'] = f'device{i}'
        device['status'] = 'default'
        response['status']['devices'].append(device)
    return response


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

@app.get("/example2/{number}")
def example2(number: int):
    return {"number": number}