[![FedCiv Lab Backend CI](https://github.com/sambyers/fedciv-lab-backend/actions/workflows/main-commit-pr.yml/badge.svg)](https://github.com/sambyers/fedciv-lab-backend/actions/workflows/main-commit-pr.yml)

# FedCiv Lab API

## Requirements
1. Python 3.10
2. Poetry

## Setup
```shell
git clone https://github.com/sambyers/fedciv-lab-backend
pip install poetry
poetry install
```
Show dependencies
```shell
poetry show -t
```

## Run app locally
```shell
poetry run flask run
```

## Test locally
```
poetry run tox
```