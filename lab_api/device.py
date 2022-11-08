import logging
from genie.libs.conf.testbed import Testbed
from pyats.topology.device import Device


# Make sure .ssh/config adds the key exchange methods the network devices support
# KexAlgorithms +diffie-hellman-group14-sha1
# Possible .ssh/config settings to avoid when certs change on network devices:
# Host *
#    StrictHostKeyChecking no
#    UserKnownHostsFile /dev/null


class DeviceLab:
    def __init__(self, testbed: Testbed) -> None:
        self.testbed = testbed
        self.default_cfg_file = testbed.custom.get("default_cfg_file")
        self.devices = self.testbed.devices
        self._cfg_diff_excludes = [
            r"(^!)",
            r"(^exec-timeout)",
            r"(^no logging console)",
            r"(^login local)",
            r"(^crypto pki certificate chain)",
            r"(^service password-encryption)",
            r"(^crypto pki trustpoint)",
            ]
        self._logger = logging.getLogger("civlab_api")
        self._reload_sleep = 300
        self._reload_timeout = 1200

    def get_status(self, device: Device) -> str:
        self._logger.info(f"Getting status of {device}...")
        diff = self.get_running_default_cfg_diff(device)
        if len(diff) > 0:
            device.status = "configured"
        else:
            device.status = "default"
        return device.status

    def get_running_default_cfg_diff(self, device: Device) -> str:
        self._logger.info("Determining difference of running "
        f"and default configurations of {device}.")
        # Check to see if the default configuration exists on device
        if self.get_default_cfg_exists(device):
            # Get the running config and parse into a dict
            device.running_cfg = device.api.get_running_config_dict()
            # Get the default config from file on flash and parse into dict
            device.default_cfg = device.api.get_config_from_file(
                device.default_dir, self.default_cfg_file
            )
            # Diff the running and default config dicts
            # Exclude config lines added by pyats and comments
            device.running_default_diff = device.api.compare_config_dicts(
                device.running_cfg,
                device.default_cfg,
                exclude=self._cfg_diff_excludes,
            )
            
        # Return differences between the configs, '' for none.
        self._logger.debug("Difference in configurations:")
        self._logger.debug(device.running_default_diff)
        return device.running_default_diff

    def get_default_cfg_exists(self, device: Device) -> bool:
        self._logger.info(f"Looking for default config on flash for {device}...")
        # Default directory based on the platform (flash:, bootflash:)
        device.default_dir = device.api.get_platform_default_dir()
        # Path of the default configuration file
        device.default_cfg_path = f"{device.default_dir}/{self.default_cfg_file}"
        # Bool for if the default configuration file exists on device
        device.default_config_exists = device.api.verify_file_exists(
            device.default_cfg_path
        )
        self._logger.info(f"Default config exists: {device.default_config_exists}")
        return device.default_config_exists

    def reset(self, device: Device) -> bool:
        """Alias for reset method"""
        diff = self.get_running_default_cfg_diff(device)
        if len(diff) > 0:
            self._logger.info(f"Resetting {device}...")
            self.reset_device_to_default(device)
            self.reload(device)
            # self.clean_device_to_default(device)
            device.reset = True
        else:
            device.reset = False
        return device.reset

    def clean_device_to_default(self, device):
        device.api.clean.apply_configuration(
            file=device.default_cfg_path,
            configure_replace=True,
        )

    def reload(self, device):
        # Reload device
        self._logger.info(f"Reloading {device}...")
        device.api.execute_reload(
            prompt_recovery=False,
            reload_creds="default",
            sleep_after_reload=self._reload_sleep,
            timeout=self._reload_timeout,
        )

    def reset_device_to_default(self, device: Device) -> bool:
        # Copy default cfg into startup
        self._logger.info(f"Resetting {device} to {device.default_cfg_path}...")
        device.api.execute_copy_to_startup_config(device.default_cfg_path)

    def reset_device_to_default_all(self) -> None:
        for device in self.testbed:
            self.reset(device)

    def get_default_cfg_exists_all(self) -> None:
        for device in self.testbed:
            self.get_default_cfg_exists(device)

    def get_running_default_cfg_diff_all(self) -> None:
        for device in self.testbed:
            self.get_running_default_cfg_diff(device)

    def get_status_all(self) -> None:
        for device in self.testbed:
            self.get_status(device)

    def connect_all(self) -> None:
        self.testbed.connect()

    def disconnect_all(self) -> None:
        self.testbed.disconnect()

    def __iter__(self):
        for device in self.testbed:
            yield device

    def __str__(self):
        print(self.devices)
