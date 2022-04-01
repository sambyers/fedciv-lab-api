from fastapi import FastAPI
from pydantic import BaseModel
from genie.testbed import load
from .services import DeviceLab


app = FastAPI()

# Response Models
class LabComponent(BaseModel):
    name: str
    status: str

class LabStatus(BaseModel):
    dnac: dict | None = None
    sdwan: dict | None = None
    ise: dict | None = None
    devices: list[dict] | None = None

class Response(BaseModel):
    status: LabStatus | None = None

# If we're using pyATS Lib, we will load the testbed that is a model of the lab.
def get_testbed():
    return load("lab_data/testbed.yaml")


# Get status of lab, e.g. default or configured.
@app.get("/status", response_model=Response)
def status():
    # device_lab = DeviceLab(get_testbed())
    # status = device_lab.get_device_status()
    
    # Make lab component model with fake dnac info
    # We normally get info from backing services that talks to the lab
    dnac = LabComponent(name='dnac1', status='default')
    # Add DNAC to lab status model
    lab_status = LabStatus(dnac=dnac, devices=[])
    # Add status model to response model
    response = Response(status=lab_status)
    # Make devices model with fake devices
    for i in range(5):
        # Make new lab component model with fake device info
        device = LabComponent(name=f'device{i}', status='default')
        # Add device model to lab_status model
        lab_status.devices.append(device)
    return response.dict()


# Reset the state of the entire lab back to default.
@app.put("/reset")
def reset():
    dnac = LabComponent(name='dnac1', status='default')
    lab_status = LabStatus(dnac=dnac)
    response = Response(status=lab_status)
    return response.dict()


@app.get("/example")
def example():
    lab = DeviceLab(get_testbed())
    lab.connect_to_all()
    lab.update_default_cfg_exists()
    return lab.get_default_cfg_exists()

@app.get("/example2/{number}")
def example2(number: int):
    return {"number": number}