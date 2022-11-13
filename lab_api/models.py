from typing import List
from pydantic import BaseModel


# RESPONSE MODELS

# /status response models
class LabComponentBase(BaseModel):
    name: str
    host: str | None = None
    backup: str | None = None


class NetworkDevice(LabComponentBase):
    default_cfg_on_flash: bool | None = None
    status: str | None = None
    error: str | None = None


class DNACModel(LabComponentBase):
    name: str = "dnac"
    last_restore: str | None = None
    restore_id: str | None = None


class vManageModel(LabComponentBase):
    name: str = "vmanage"
    last_restore: str | None = None
    restore_file: str | None = None


class ISEModel(LabComponentBase):
    name: str = "ise"
    last_restore: str | None = None
    restore_file: str | None = None
    status: str | None = None


class LabStatus(BaseModel):
    dnac: DNACModel | None = None
    vmanage: vManageModel | None = None
    ise: ISEModel | None = None
    devices: List[NetworkDevice] | None = None
    error: str | None = None


class StatusResponse(BaseModel):
    status: LabStatus | None = None


# /list response models
class ListItem(BaseModel):
    name: str
    host: str


class ListResponse(BaseModel):
    appliances: List[ListItem]
    network_devices: List[ListItem]


# Task queue job status response models
class JobStatus(BaseModel):
    id: str
    status: str | None = None
    result: str | None = None
    disposition: str | None = None


class JobError(BaseModel):
    error: str


class JobResponse(BaseModel):
    job: JobStatus
    error: JobError | None = None


class MultiJobResponse(BaseModel):
    responses: List[JobResponse]


# /reset response model
class ResetResponse(BaseModel):
    reset: bool | None = None
