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
7. Docker

## Deploy

Git pull this repo:
```shell
git pull https://github.com/sambyers/fedciv-lab-api
```

Create a lab_data directory and put in lab inventory yaml files. testbed.yaml and appliances.yaml are required.

Look at the /mock_data directory for an example.

Run deploy script:
```shell
./scripts/deploy.sh
```