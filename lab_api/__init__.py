from time import sleep
from typing import Callable
from rq.job import Job
from rq.exceptions import NoSuchJobError
from .ise import ISE
from .device import DeviceLab
from .services import DNAC, vManage, Appliance
from .config import (
    app,
    REDIS_CONN,
    logger,
    DEFAULT_Q,
    NETDEVICE_TESTBED,
    APPLIANCES,
    HTTPException,
)
from .models import (
    ISEModel,
    JobError,
    LabStatus,
    DNACModel,
    ListItem,
    ListResponse,
    NetworkDevice,
    StatusResponse,
    JobResponse,
    JobStatus,
    vManageModel,
    BaseModel,
    MultiJobResponse,
)


def get_appliance_obj(name: str) -> Appliance:
    name.lower()
    params = APPLIANCES.get(name)
    args = [
        params["host"],
        params["username"],
        params["password"],
        params["port"],
    ]
    match name:
        case "dnac":
            obj = DNAC(*args)
        case "ise":
            obj = ISE(*args)
        case "vmanage":
            obj = vManage(*args)
    return obj


# LAB TASKS


def task_get_dnac_status() -> DNACModel:
    dnac = get_appliance_obj("dnac")
    dnac.connect()
    resp = dnac.get_status()
    dnac.disconnect()
    return DNACModel(**resp)


def task_get_vmanage_status() -> vManageModel:
    vmanage = get_appliance_obj("vmanage")
    vmanage.connect()
    resp = vmanage.get_status()
    vmanage.disconnect()
    return vManageModel(**resp)


def task_get_ise_status() -> ISEModel:
    host = APPLIANCES["ise"]["host"]
    username = APPLIANCES["ise"]["username"]
    password = APPLIANCES["ise"]["password"]
    version = APPLIANCES["ise"]["version"]
    ise = ISE(
        host,
        username,
        password,
        version,
    )
    resp = ise.get_status()
    return ISEModel(**resp)


def task_get_network_device_status(name: str) -> NetworkDevice:
    """Get network device status"""
    device_lab = DeviceLab(NETDEVICE_TESTBED)
    selectedDevice = device_lab.devices.get(name)
    if selectedDevice:
        logger.info(f"Connecting to: {selectedDevice.name}")
        selectedDevice.connect()
        status = device_lab.get_status(selectedDevice)
        selectedDevice.disconnect()
        result = NetworkDevice(
            name=selectedDevice.name,
            status=status,
            host=str(selectedDevice.connections.ssh.ip),
            default_cfg_on_flash=selectedDevice.default_config_exists,
        )
    else:
        result = NetworkDevice(name=name, error="Device not found.")
    return result


def net_device_model_packing(device):
    return NetworkDevice(
        name=device.name,
        status=device.status,
        host=str(device.connections.ssh.ip),
        default_cfg_on_flash=device.default_config_exists,
    )


def task_get_network_device_status_all() -> list[NetworkDevice]:
    """Get all network devices status"""
    devices = []
    device_lab = DeviceLab(NETDEVICE_TESTBED)
    device_lab.connect_all()
    device_lab.get_status_all()
    # for device in device_lab:
    #     net_device = NetworkDevice(
    #         name=device.name,
    #         status=device.status,
    #         host=str(device.connections.ssh.ip),
    #         default_cfg_on_flash=device.default_config_exists,
    #     )
    #     devices.append(net_device)
    devices = [net_device_model_packing(device) for device in device_lab.devices]
    logger.debug(devices)
    device_lab.disconnect_all()
    return devices


def task_reset_network_device_all():
    device_lab = DeviceLab(NETDEVICE_TESTBED)
    device_lab.connect_all()
    device_lab.reset_device_to_default_all()
    device_lab.disconnect_all()
    return True


def task_reset_network_device(name: str) -> bool:
    logger.info("Resetting a network device.")
    device_lab = DeviceLab(NETDEVICE_TESTBED)
    logger.info("Device lab init.")
    logger.info(f"Searching for network device {name}")
    device = device_lab.devices.get(name)
    if device:
        logger.info(f"Found network device: {device.name}")
        logger.info(f"Connecting to: {device.name}")
        device.connect()
        reset_resp = device_lab.reset(device)
        device.disconnect()
    else:
        logger.info(f"Found no network device: {name}")
        logger.info("No reset.")
        reset_resp = False
    return reset_resp


def task_reset_dnac():
    id = APPLIANCES["dnac"]["backup_id"]
    dnac = get_appliance_obj("dnac")
    dnac.connect()
    resp = dnac.reset(id)
    dnac.disconnect()
    return resp


def task_reset_vmanage() -> str:
    backup_path = APPLIANCES["vmanage"]["backup_path"]
    vmanage = get_appliance_obj("vmanage")
    vmanage.connect()
    resp = vmanage.reset(backup_path)
    vmanage.disconnect()
    return resp


def task_reset_ise() -> tuple:
    host = APPLIANCES["ise"]["host"]
    username = APPLIANCES["ise"]["username"]
    password = APPLIANCES["ise"]["password"]
    version = APPLIANCES["ise"]["version"]
    file = APPLIANCES["ise"]["backup_file"]
    repo = APPLIANCES["ise"]["backup_repo"]
    key = APPLIANCES["ise"]["backup_key"]
    ise = ISE(
        host,
        username,
        password,
        version,
    )
    # Make sure the password to the repo is set correctly
    # It becomes unset after a restore
    # update, msg = ise.update_repo_pass(repo, repo_pass)
    # if not update:
    #     return (update, msg)
    resp = ise.reset(file, repo, key)
    return resp


# TASK DISPATCH
# Dispatch functions used to standardize getting job results from cache,
# handle exceptions, and logging.
# Using ame job_id = get cached results when available
# Use consistent job_id for each task to use the queue as a cache and protect
# the services (lab appliance being automated) from being overrun by jobs.

# Run job and wait for results
# Useful for short running jobs, e.g. get_status tasks
# Why use for short jobs? Cache and protect device being automated
# Timeout is how long to run the job
# TTL is how long to cache the results
def rq_dispatcher_run(
    task: Callable,
    id: str = None,
    args: tuple = None,
    timeout: str = "10m",
    ttl: int = 30,
    cache: bool = True,
) -> BaseModel:
    logger.info(f"Running job to completion: {task}")
    if not cache:
        logger.info("Not using cached job result.")
        job = DEFAULT_Q.enqueue(
            task, job_id=id, args=args, result_ttl=ttl, job_timeout=timeout
        )
        job = rq_job_wait(job)
    else:
        try:
            logger.info("Looking up cached job result.")
            job = Job.fetch(id, connection=REDIS_CONN)
            if not job.result:
                raise NoSuchJobError
        except NoSuchJobError as e:
            logger.info("No cached job result.")
            logger.debug(e)
            job = DEFAULT_Q.enqueue(
                task, job_id=id, args=args, result_ttl=ttl, job_timeout=timeout
            )
            job = rq_job_wait(job)
    logger.debug(job)
    logger.info(f"Job status: {job.get_status()}.")
    logger.info(job.result)
    return job.result


# Wait around until job is done
def rq_job_wait(job: Job, wait: int = 2) -> Job:
    while not job.result:
        logger.info(f"Waiting on job {job.id} to finish...")
        sleep(wait)
    return job


def rq_job_wait_multi(jobs: list, wait: int = 2) -> None:
    run = True
    while run is True:
        sleep(wait)
        i = 0
        for job in jobs:
            if job.result:
                i += 1
            if i == len(jobs):
                run = False
                break


# Queue job and return job ID for checking status later
# Useful for long running jobs, e.g. reset tasks
def rq_dispatcher_enq(
    task: Callable,
    id: str = None,
    args: tuple = None,
    timeout: str = "1h",
    ttl: int = 600,
    cache: bool = True,
) -> JobResponse:
    logger.info(f"Queuing job: {task}")
    if not cache:
        logger.info("Not using cached job result.")
        job = DEFAULT_Q.enqueue(
            task, job_id=id, args=args, result_ttl=ttl, job_timeout=timeout
        )
    else:
        try:
            logger.info("Looking up cached job result.")
            job = Job.fetch(id, connection=REDIS_CONN)
        except NoSuchJobError as e:
            logger.info("No cached job result.")
            logger.debug(e)
            job = DEFAULT_Q.enqueue(
                task, job_id=id, args=args, result_ttl=ttl, job_timeout=timeout
            )
        if job.result:
            job_status = JobStatus(
                id=job.id,
                status=job.get_status(),
                result=str(job.result),
                # disposition=job.result[1],
            )
        else:
            job_status = JobStatus(id=job.id, status=job.get_status())
    logger.debug(job)
    logger.info(f"Job status: {job.get_status()}.")
    logger.info(job_status)
    return JobResponse(job=job_status)


def rq_dispatcher_multi_enq(task_map):
    job_ids = task_map.keys()
    results = {}
    # Check the queue and see if there are cached results
    jobs = Job.fetch_many(job_ids, connection=REDIS_CONN)
    # Stash the cached results
    for job in jobs:
        if job and job.get_status() == "finished":
            results[job.id] = job.result
    # Process jobs without results
    if not len(job_ids) == len(results):
        new_jobs = []
        for id, func in task_map.items():
            # We only want to run tasks we don't have results for
            if id not in results.keys():
                job = DEFAULT_Q.enqueue(func, job_id=id)
                new_jobs.append(job)
        rq_job_wait_multi(new_jobs)
        results.update({job.id: job.result for job in new_jobs})
    return results


# ROUTES
@app.get("/list", response_model=ListResponse)
def list():
    """List all of the devices in the lab."""
    appliance_items = []
    for k, v in APPLIANCES.items():
        item = ListItem(name=k, host=v.get("host"))
        appliance_items.append(item)
    device_items = []
    for device in NETDEVICE_TESTBED:
        item = ListItem(name=device.name, host=str(device.connections.ssh.ip))
        device_items.append(item)
    return ListResponse(appliances=appliance_items, network_devices=device_items)


@app.get("/status", response_model=StatusResponse, response_model_exclude_unset=True)
def status():
    # Common job id to task mapping
    task_map = {
        "netdevices_status": task_get_network_device_status_all,
        "dnac_status": task_get_dnac_status,
        "vmanage_status": task_get_vmanage_status,
        "ise_status": task_get_ise_status,
    }
    results = rq_dispatcher_multi_enq(task_map=task_map)
    for dev_result in results["netdevices_status"]:
        dev_result.host= str(dev_result.host)
    logger.info("Results from status all: ", results)
    lab_status = LabStatus()
    lab_status.devices = results["netdevices_status"]
    lab_status.dnac = results["dnac_status"]
    lab_status.vmanage = results["vmanage_status"]
    lab_status.ise = results["ise_status"]
    return StatusResponse(status=lab_status)


@app.get(
    "/status/vmanage", response_model=StatusResponse, response_model_exclude_unset=True
)
def get_status_vmanage():
    lab_status_resp = LabStatus(
        vmanage=rq_dispatcher_run(task_get_vmanage_status, id="vmanage_status")
    )
    return StatusResponse(status=lab_status_resp)


@app.get(
    "/status/dnac", response_model=StatusResponse, response_model_exclude_unset=True
)
def get_status_dnac():
    lab_status = LabStatus(
        dnac=rq_dispatcher_run(task_get_dnac_status, id="dnac_status")
    )
    return StatusResponse(status=lab_status)


@app.get(
    "/status/ise", response_model=StatusResponse, response_model_exclude_unset=True
)
def get_status_ise():
    # Not using queue because we're talking to ISE API
    # ise=rq_dispatcher_run(task_get_ise_status, id="ise_status")
    ise = task_get_ise_status()
    lab_status = LabStatus(ise=ise)
    return StatusResponse(status=lab_status)


# Status for all network devices in lab
@app.get(
    "/status/network-devices",
    response_model=StatusResponse,
    response_model_exclude_unset=True,
)
def get_status_network_devices():
    """
    Get status for all autonomous network devices.
    """
    lab_status = LabStatus()
    lab_status.devices = rq_dispatcher_run(
        task_get_network_device_status_all, id="netdevices_status"
    )
    return StatusResponse(status=lab_status)


# Wildcard status route for network devices
@app.get(
    "/status/{name}", response_model=StatusResponse, response_model_exclude_unset=True
)
def get_status_network_device(name: str):
    """
    Get status for a single autonomous network device based on hostname.
    """
    name.lower()
    netdevice = rq_dispatcher_run(
        task_get_network_device_status, id=f"{name}_status", args=(name,)
    )
    lab_status = LabStatus()
    if netdevice.error:
        lab_status.error = netdevice.error
        lab_status.devices = [netdevice]
    else:
        lab_status.devices = [netdevice]
    return StatusResponse(status=lab_status)


# Retrieve status of job given the job ID
@app.get("/job/{jobID}", response_model=JobResponse, response_model_exclude_unset=True)
def get_job_status(jobID: str):
    """
    Get the status of queued jobs.
    """
    try:
        job = Job.fetch(jobID, connection=REDIS_CONN)
        if job.result:
            job_status = JobStatus(
                id=job.id,
                status=job.get_status(),
                result=str(job.result),
                # disposition=job.result[1],
            )
        else:
            job_status = JobStatus(id=job.id, status=job.get_status())
        return JobResponse(job=job_status)
    except NoSuchJobError:
        raise HTTPException(status_code=404, detail="No job found.")


# Reset the state of the entire lab back to default.
@app.put(
    "/reset",
    response_model=MultiJobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset():
    # timeout = "1h"
    responses = []
    ise = rq_dispatcher_enq(task_reset_ise, id="reset_ise")
    vmanage = rq_dispatcher_enq(task_reset_vmanage, id="reset_vmanage")
    dnac = rq_dispatcher_enq(task_reset_dnac, id="reset_dnac")
    netdevices = rq_dispatcher_enq(task_reset_network_device_all, id="reset_netdevices")
    responses.append(ise)
    responses.append(vmanage)
    responses.append(dnac)
    responses.append(netdevices)
    return MultiJobResponse(responses=responses)


# Reset the state of the entire lab back to default.
@app.put(
    "/reset/dnac",
    response_model=JobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset_dnac():
    return rq_dispatcher_enq(task_reset_dnac, id="reset_dnac")


# Reset the state of the entire lab back to default.
@app.put(
    "/reset/ise",
    response_model=JobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset_ise():
    # return rq_dispatcher_enq(task_reset_ise, id="reset_ise")
    # Migrated to using the ISE OpenAPI and don't need to use task queue any longer.
    r, m = task_reset_ise()
    if not r:
        j_err = JobError(error=m)
        j_stat = JobStatus(id="reset_ise")
        resp = JobResponse(job=j_stat, error=j_err)
    else:
        j_stat = JobStatus(id="reset_ise", result=m)
        resp = JobResponse(job=j_stat)
    return resp


# Reset the state of the entire lab back to default.
@app.put(
    "/reset/vmanage",
    response_model=JobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset_vmanage():
    return rq_dispatcher_enq(task_reset_vmanage, id="reset_vmanage")


@app.put(
    "/reset/network-devices",
    response_model=JobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset_network_devices():
    return rq_dispatcher_enq(task_reset_network_device_all, id="reset_netdevices")


# Reset a specified lab device
@app.put(
    "/reset/{name}",
    response_model=JobResponse,
    response_model_exclude_unset=True,
    status_code=201,
)
def reset_network_device(name: str):
    name.lower()
    return rq_dispatcher_enq(
        task_reset_network_device, id=f"{name}_reset", args=(name,)
    )
