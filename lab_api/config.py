from os import environ, getenv
from logging import getLogger
from logging.config import dictConfig
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from redis import Redis
from rq import Queue
from genie.testbed import load as testbed_load
from yaml import load as yamlload
from yaml import Loader as yamlLoader


# Config and setup
REDIS_CONN = Redis(host="redis", port=6379)
DEFAULT_Q = Queue(connection=REDIS_CONN)
NETDEVICE_TESTBED = testbed_load(getenv("CIVLAB_NETDEVICE_DATA"))
with open(getenv("CIVLAB_APPLIANCE_DATA"), "r") as stream:
    APPLIANCES = yamlload(stream, Loader=yamlLoader)
API_KEY = environ["CIVLAB_API_KEY"]
api_key_header_auth = APIKeyHeader(name="access_token", auto_error=True)


def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )


# Source:
# https://stackoverflow.com/questions/63510041/
# adding-python-logging-to-fastapi-endpoints-hosted-on-docker-doesnt-display-api
# Logging Config Model
class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "civlab_api"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    }
    loggers = {
        "civlab_api": {"handlers": ["default"], "level": LOG_LEVEL},
    }


dictConfig(LogConfig().dict())
logger = getLogger("civlab_api")

app = FastAPI(dependencies=[Depends(get_api_key)])
