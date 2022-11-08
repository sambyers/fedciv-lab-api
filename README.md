[![FedCiv Lab Backend CI](https://github.com/sambyers/fedciv-lab-backend/actions/workflows/main-commit-pr.yml/badge.svg)](https://github.com/sambyers/fedciv-lab-backend/actions/workflows/main-commit-pr.yml)

# FedCiv Lab API

## **In Development**
[Backlog](BACKLOG.md)

## Requirements
1. Python 3.10
2. FastAPI
3. pyATS Library
4. Paramiko
5. RQ
6. Redis

## Deploy

This deployment script zips up the local directory, copies to the target server, and runs docker-compose to bring up the API service. The script will prompt for the sudo password multiple times to run remote commands on the remote server.

```shell
./scripts/deploy.sh
IP of server?
10.1.1.1
Username?
admin
...
```

If this service gets any more serious, we should migrate to a real container solution.

## Dev Setup
### Setup with Poetry
```shell
git clone https://github.com/sambyers/fedciv-lab-backend
pip install poetry
poetry install
```
Show dependencies
```shell
poetry show -t
```

### Setup with Pip
```shell
git clone https://github.com/sambyers/fedciv-lab-backend
pip install -r requirements.txt
```

## Run app locally
### Run with live network devices in lab
Without Docker:
```shell
./start
```

With Docker:
```shell
docker-compose up -d
```

Example of scaling with Docker:
```shell
docker-compose up -d --scale api=2 rq-worker=2
```

Traefik will automatically load balance multiple API containers.

### Run with mock network devices for testing
Connecting to the network devices in the lab is an expensive operation, so using the mock argument loads a mock testbed of devices to do testing on just the appliances in the lab.

```shell
./start.sh mock
```

When running in docker, this is configured in the Dockerfile.

## Test locally
```shell
poetry run tox
```
Or
```shell
tox
```