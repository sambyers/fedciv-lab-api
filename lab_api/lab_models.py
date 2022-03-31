from genie.libs.conf.testbed import Testbed


# Add models of the lab and lab components.
# Wrap device and platform automation with classes to simplify usage.
# This is an example of modeling the lab and adding a pyATS testbed object.
# The pyATS testbed obj gives us methods to interact with devices in the lab.
class Lab:
    def __init__(self, testbed: Testbed) -> None:
        self.testbed = testbed

    def get_device_status(self):
        pass

    def check_default_cfg_exists(self):
        """
        Side effect: add attribute to device obj
        default_cfg_exists = True|False
        """
        cfg_path = self.testbed.custom["default_cfg_path"]
        for device in self.testbed:
            device.default_config_exists = device.api.verify_file_exists(cfg_path)

    def connect_to_devices(self) -> None:
        for device in self.testbed:
            device.connect()
