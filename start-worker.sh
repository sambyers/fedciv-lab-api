#!/bin/bash
# Dummy key for lab_api to be used as a module by RQ worker
export CIVLAB_API_KEY=DUMMY
if [ "$1" == "mock" ]; then
    # Mock testbed if arg 1 is mock
    export CIVLAB_NETDEVICE_DATA=mock_data/testbed.yaml
    export CIVLAB_APPLIANCE_DATA=mock_data/appliances.yaml
else 
    # Prod testbed
    export CIVLAB_NETDEVICE_DATA=lab_data/testbed.yaml
    export CIVLAB_APPLIANCE_DATA=lab_data/appliances.yaml
fi
# Start RQ worker
rq worker -u redis://redis:6379
