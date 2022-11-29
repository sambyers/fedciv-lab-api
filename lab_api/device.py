import logging
# from datetime import datetime
from genie.libs.conf.testbed import Testbed
from pyats.topology.device import Device


# Make sure .ssh/config adds the key exchange methods the network devices support
# KexAlgorithms +diffie-hellman-group14-sha1
# Possible .ssh/config settings to avoid when certs change on network devices:
# Host *
#    StrictHostKeyChecking no
#    UserKnownHostsFile /dev/null


class DeviceLab:
    """Class to connect to lab devices"""
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
        self._backup_prefix = "cpoc_backup_"

    def get_status(self, device: Device) -> str:
        """Get the device config status: default or configured
        
        args:
            device: string name of the device to reset
        returns:
            status: configured or default
        """
        self._logger.info(f"Getting status of {device}...")
        diff = self.get_running_default_cfg_diff(device)
        if len(diff) > 0:
            device.status = "configured"
        else:
            device.status = "default"
        return device.status

    def get_running_default_cfg_diff(self, device: Device) -> str:
        """Get diff between default config and running
        
        args:
            device: string name of the device to reset
        returns:
            running_default_diff: string diff between running and default cfg
        """
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
        """Determine if the device has the default config on flash
        
        args:
            device: string name of the device to reset
        returns: bool
        """
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

    def is_file_on_flash(self, device: Device, filename: str) -> bool:
        """Determine if a file is on the device flash

        args:
            device: string name of the device to reset
            filename: string filename to look for
        return: bool
        
        """
        self._logger.info(f"Verifying default director for {device}.")
        device.default_dir = device.api.get_platform_default_dir()
        path = f"{device.default_dir}/{filename}"
        self._logger.info(f"Verifying if {path} is on flash of {device}.")
        exists = device.default_config_exists = device.api.verify_file_exists(path)
        self._logger.info(f"{filename} exists on {device} at {path}: {exists}")
        return exists

    def reset(self, device: Device) -> bool:
        """Reset Device
        
        args:
            device: string name of the device to reset
        returns: bool
        """
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

    def reload(self, device) -> None:
        """Reload the device

        args:
            device: string name of the device to reload
        """
        self._logger.info(f"Reloading {device}...")
        device.api.execute_reload(
            prompt_recovery=False,
            reload_creds="default",
            sleep_after_reload=self._reload_sleep,
            timeout=self._reload_timeout,
        )

    def reset_device_to_default(self, device: Device) -> None:
        """Reset device to default configuration

        args:
            device: string name of the device to reload
        """
        self._logger.info(f"Resetting {device} to {device.default_cfg_path}...")
        device.api.execute_copy_to_startup_config(device.default_cfg_path)

    def backup(self, device: Device, cust_id: str) -> bool:
        """Backup the device configuration

        args:
            device: string name of the device to reload
        returns: bool
        """
        backup_file = self.backup_running_to_flash(device, cust_id)
        return self.is_file_on_flash(device, backup_file)
    
    def backup_running_to_flash(self, device: Device, cust_id: str) -> str:
        """Backup the running configuration to flash

        args:
            device: string name of the device to reload
            cust_id: string identifier of the backed up config
        returns:
            backup_fn: string name of the backed up file
        """
        self._logger.info(f"Backing up running configuration to flash on {device}...")
        # timestamp = datetime.now().isoformat(timespec='seconds')
        backup_fn = f"{self._backup_prefix}{cust_id}.cfg"
        device.api.clean.copy_run_to_flash(file_name=backup_fn)
        return backup_fn

    def backup_running_to_flash_all(self, cust_id: str) -> None:
        """Backup running config on all devices"""
        for device in self.testbed:
            self.backup_running_to_flash(device, cust_id)

    def reset_device_to_default_all(self) -> None:
        """Reset config to default on all devices"""
        for device in self.testbed:
            self.reset(device)

    def get_default_cfg_exists_all(self) -> None:
        """Confirm default config is on all devices"""
        for device in self.testbed:
            self.get_default_cfg_exists(device)

    def get_running_default_cfg_diff_all(self) -> None:
        """Get diff between running and default cfg"""
        for device in self.testbed:
            self.get_running_default_cfg_diff(device)

    def get_status_all(self) -> None:
        """Get config status of all devices"""
        for device in self.testbed:
            self.get_status(device)

    def connect_all(self) -> None:
        """Connect to all devices via SSH"""
        self.testbed.connect()

    def disconnect_all(self) -> None:
        """Disconnect SSH from all devices"""
        self.testbed.disconnect()

    def __iter__(self) -> Device:
        for device in self.testbed:
            yield device

    def __repr__(self) -> str:
        return f"DeviceLab({self.testbed})"

    def __str__(self) -> str:
        return str(self.devices)
