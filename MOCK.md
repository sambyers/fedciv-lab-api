# Make a mock device

## Environment vars
```shell
# Your testbed here.
export PYATS_TESTBED="lab_data/sb_testbed.yaml"
export UNICON_RECORD=recording
```

## 
Run code that connects to devices to capture recording

## Create mock from recording with cmd below
```shell
poetry run python -m unicon.playback.mock --recorded-data recording1/csr1000v-1 --output mock_data/iosxe/csr1000v-1.yaml
```