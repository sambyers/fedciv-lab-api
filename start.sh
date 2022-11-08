#!/bin/bash
# Read API key
key=$(<CIVLAB_API_KEY)
export CIVLAB_API_KEY=$key
if [ "$1" == "mock" ]; then
    # Mock testbed if arg 1 is mock
    export CIVLAB_NETDEVICE_DATA=mock_data/testbed.yaml
    export CIVLAB_APPLIANCE_DATA=mock_data/appliances.yaml
else 
    # Prod testbed
    export CIVLAB_NETDEVICE_DATA=lab_data/testbed.yaml
    export CIVLAB_APPLIANCE_DATA=lab_data/appliances.yaml
fi
# Start API
uvicorn lab_api:app --host=0.0.0.0 --port=80 --proxy-headers
