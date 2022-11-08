from genie.testbed import load

tb = load("mock_data/mock.yaml")
device = tb.devices["csr1000v-1"]
device.connect()
device.api.execute_reload(
    prompt_recovery=False, reload_creds="default", sleep_after_reload=3, timeout=20
)
