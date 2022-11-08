#!/bin/bash
docker build . -t civlab-api:test -f ./tests/Dockerfile --platform linux/amd64 && docker run --rm civlab-api:test tox; docker image rm civlab-api:test 