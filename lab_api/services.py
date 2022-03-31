# Module to hold the services to interact with the lab itself.

# For network devices in the lab
from genie.libs.conf.testbed import Testbed

# For DNAC. We may just need to hit the SSH shell, tho.
# If just shell, use paramiko to execute a local shell/python script or run commands.
# from dnacentersdk import api

# For vManage
# Possibilities:
# https://github.com/CiscoDevNet/sastre
# This seems to have backup and restore built in.

# https://github.com/CiscoDevNet/python-viptela
# Nice clean vManage capability. We could model the default config in code, clean, and
# reset to default via the API.

# Add models of the lab and lab components.
# Wrap device and platform automation with classes to simplify usage.
# This is an example of modeling the lab and adding a pyATS testbed object.
# The pyATS testbed obj gives us methods to interact with devices in the lab.
class DeviceLab:
    def __init__(self, testbed: Testbed) -> None:
        self.testbed = testbed

    def get_default_cfg_exists(self) -> dict:
        results = {}
        for device in self.testbed:
            results[device.name] = device.default_config_exists
        return results

    def update_default_cfg_exists(self):
        """
        Side effect: add attribute to device obj
        default_cfg_exists = True|False
        """
        cfg_path = self.testbed.custom["default_cfg_path"]
        for device in self.testbed:
            device.default_config_exists = device.api.verify_file_exists(cfg_path)

    def connect_to_all(self) -> None:
        for device in self.testbed:
            device.connect()

