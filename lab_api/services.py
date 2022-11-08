import logging
from re import compile as re_compile
from time import sleep
from socket import error as socket_error
# from abc import ABC
import paramiko
from genie.libs.conf.testbed import Testbed
from pyats.topology.device import Device
# from ciscoisesdk import IdentityServicesEngineAPI
# from ciscoisesdk.exceptions import ciscoisesdkException, ApiError


logger = logging.getLogger("civlab_api")


# Make sure .ssh/config adds the key exchange methods the network devices support
# KexAlgorithms +diffie-hellman-group14-sha1
# Possible .ssh/config settings to avoid when certs change on network devices:
# Host *
#    StrictHostKeyChecking no
#    UserKnownHostsFile /dev/null

# Not in use, migrated to device.py
class DeviceLab:
    def __init__(self, testbed: Testbed) -> None:
        self.testbed = testbed
        self.default_cfg_file = testbed.custom.get("default_cfg_file")


    def get_status(self, device: Device) -> str:
        diff = self.get_running_default_cfg_diff(device)
        if len(diff) > 0:
            device.status = "configured"
            return device.status
        else:
            device.status = "default"
            return device.status

    def get_running_default_cfg_diff(self, device: Device) -> str:
        # Check to see if the default configuration exists on device
        if self.get_default_cfg_exists(device):
            # Get the running config and parse into a dict
            device.running_cfg = device.api.get_running_config_dict()
            # Get the default config from file on flash and parse into dict
            device.default_cfg = device.api.get_config_from_file(
                device.default_dir, self.default_cfg_file
            )
            # Diff the running and default config dicts
            device.running_default_diff = device.api.compare_config_dicts(
                device.running_cfg, device.default_cfg
            )
        # Return differences between the configs, '' for none.
        return device.running_default_diff

    def get_default_cfg_exists(self, device: Device) -> bool:
        # Default directory based on the platform (flash:, bootflash:)
        device.default_dir = device.api.get_platform_default_dir()
        # Path of the default configuration file
        device.default_cfg_path = f"{device.default_dir}/{self.default_cfg_file}"
        # Bool for if the default configuration file exists on device
        device.default_config_exists = device.api.verify_file_exists(
            device.default_cfg_path
        )
        return device.default_config_exists

    def reset_device_to_default(
        self, device: Device, sleep: int = 120, timeout: int = 800
    ) -> bool:
        # Grab the diff between the running cfg and default cfg
        diff = self.get_running_default_cfg_diff(device)
        if len(diff) > 0:
            # Copy running cfg into startup
            device.api.execute_copy_to_startup_config(device.default_cfg_path)
            # Reload device
            device.api.execute_reload(
                prompt_recovery=False,
                reload_creds="default",
                sleep_after_reload=sleep,
                timeout=timeout,
            )
            device.reset = True
        else:
            device.reset = False
        # Return True if we reset the device, False if we didn't.
        return device.reset

    def reset_device_to_default_all(self, sleep: int = 120, timeout: int = 800) -> None:
        for device in self.testbed:
            self.reset_device_to_default(device, sleep=sleep, timeout=timeout)

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


class Appliance:
    def __init__(self, host: str, username: str, password: str, port: int):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.status = None
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
        self._shell = None
        self._last_cmd = None
        self._logout_cmd = "exit"

    def get_status():
        # Implement in child class
        pass

    def reset():
        # Implement in child class
        pass

    def connect(self) -> bool:
        logger.info(f"Connecting to {self.host}:{self.port}")
        self.connected = self._connect()
        return self.connected

    def _connect(self):
        """Connection adapter"""
        self._do_before_connect()
        conn_result = self._connect_ssh()
        self._do_after_connect()
        return conn_result

    def _do_before_connect(self) -> None:
        # Implement in child class
        pass

    def _do_after_connect(self) -> None:
        # Implement in child class
        pass

    def _connect_ssh(self) -> bool:
        """Connect via Paramiko client and invoke a shell"""
        self._ssh.connect(self.host, self.port, self.username, self.password)
        self._shell = self._ssh.invoke_shell()
        return True

    def disconnect(self) -> bool:
        if self.connected:
            self.connected = self._disconnect()
        return self.connected

    def _disconnect(self) -> bool:
        """Disconnection adapter"""
        self._do_before_disconnect()
        self._ssh.close()
        self._do_after_disconnect()
        return False

    def _do_before_disconnect(self) -> None:
        # Override as needed
        self._send_command(self._logout_cmd)

    def _do_after_disconnect(self) -> None:
        # Implement in child class
        pass

    def _check_connection(self) -> bool:
        try:
            if self._shell.closed is False:
                return True
        except AttributeError:
            return False

    def _send_command(self, cmd: str, bytes: int = 20000, wait: int = 4) -> str:
        """Sends commands via ssh shell

        Args:
            cmd (str): Command to send to the shell
            wait (int): Time in seconds to wait after sending the command
                (default is 4)

        Returns:
            str: response read off the ssh shell decoded in utf-8
        """
        try:
            logger.info(f"Sending command: {cmd}")
            self._last_cmd = cmd
            cmd = cmd + "\n"
            self.last_cmd = cmd
            sent_bytes = self._shell.send(cmd)
            # Confirm entire command was sent to the shell
            assert sent_bytes == len(cmd.encode("utf-8"))
            # Read bytes off channel
            resp = self._read_shell(bytes=bytes, wait=wait)
            logger.info("Response:")
            logger.info(resp)
            # Return decoded bytes as str
            return resp
        except (
            paramiko.BadHostKeyException,
            paramiko.AuthenticationException,
            paramiko.SSHException,
            socket_error,
        ) as error:
            return error

    def _read_shell(self, bytes: int = 20000, wait: int = 4) -> str:
        """Read bytes off of ssh shell, decode in utf-8"""
        logger.info("Reading from shell channel...")
        if wait > 0:
            sleep(wait)
        else:
            return "Shell read timeout. No data received on shell/channel."
        if self._shell.recv_ready():
            return self._shell.recv(bytes).decode("utf-8")
        return self._read_shell(bytes, wait // 2)

    def _wait_on_restore(
        self,
        success_substr: str,
        fail_substr: str,
        wait: int = 180,
        interval: int = 1,
    ) -> tuple:
        """Waits on response from shell and checks if the success sub string arg is present.
        wait is seconds to wait per interval.

        Args:
            started_substr (str): Sub string indicating the restore has started
            success_substr (str): Sub string that will be in response for a success
            fail_substr (str): Sub string that will be in response for a failure
            wait (int): Seconds to wait for response
            interval (int): Number of times to wait
        Returns:
            tuple:
                (bool) If restore was successful or not
                (str) Message indicating disposition
        """
        total_wait_time_mins = str(wait * interval // 60)
        logger.info(f"Waiting for restore operation for {total_wait_time_mins} mins")
        while interval > 0:
            wait_time_left = str(wait * interval // 60)
            logger.debug(f"Waiting {wait_time_left} more minutes until timeout.")
            sleep(wait)
            logger.info("Checking if restore complete...")
            # Read 100K bytes off the channel because when restoring
            # there's a lot of output
            logger.info("Reading from channel...")
            resp = self._read_shell(bytes=100000)
            logger.debug(resp)
            if success_substr in resp:
                logger.info("Restore successful.")
                return True, "Restore successful."
            elif fail_substr in resp:
                logger.info("Restore failed.")
                return False, "Restore failed."
            interval -= 1
        logger.info("Determining restore status timed out.")
        return False, "Timeout. Restore may or may not be successful."
    
    def str_has_time(self, s: str) -> bool:
        pattern = re_compile(r".*\d:\d\d:\d\d.*")
        if pattern.match(s):
            return True
        else:
            return False


class DNAC(Appliance):
    def __init__(self, host, username, password, port):
        super().__init__(host, username, password, port)
        self._check_cmd = "more /etc/os-release"
        self._status_cmd = "maglev restore history"
        self._kong_username = "admin"
        self._kong_username_prompt = "[administration] username"
        self._kong_password_prompt = "[administration] password"
        self._restore_history_fragment = "RESTORE.FINALIZE_RESTORE"
        self._default_result = {
            "last_restore": "None found",
            "restore_id": "None found",
            "status": "No restore history found",
            "host": self.host,
        }
        self._restore_success = "Scheduled restore of backup '93c5643c-f3e0-4bae-a283-5e0210f7e68d"
        self._restore_fail = "fail"

    def reset(self, backup_id: str):
        # Not tested at all
        logger.info("Restoring DNAC...")
        restore_cmd = "maglev restore apply " + backup_id
        logger.info("Sending restore command to DNAC...")
        response = self._send_command(restore_cmd)
        logger.debug(f"DNAC response: {response}")
        resp = self._handle_kong_prompt(response)
        logger.debug(f"Response after handling credential prompt: {resp}")
        logger.info("Checking for response from DNAC...")
        return self._wait_on_restore(
            self._restore_success,
            self._restore_fail,
            wait=300,
            interval=8,
        )

    def get_status(self) -> list:
        # Tested and works
        resp = self._send_command(self._status_cmd)
        resp = self._handle_kong_prompt(resp)
        self.status = self._parse_maglev_restore_history(resp, self._default_result)
        return self.status

    def _parse_maglev_restore_history(self, s: str, r: dict) -> dict:
        lines = s.split("\n")
        results = [line for line in lines if self._restore_history_fragment in line]
        if results:
            result = results.pop(-1)
            result = result.split()
            # Ex. ['2022-03-22', '21:23:09', 'ee84abae-a11b-45c6-94c3-d578cfe888f6',
            # 'RESTORE.FINALIZE_RESTORE', 'SUCCESS']
            # Restore ID is 36 chars
            for word in result: 
                if len(word) == 36: r["restore_id"] = word
                if self.str_has_time(word): r["last_restore"] = f"{result[0]} {word}"
                else: r["last_restore"] = result[0]
            r["status"] = result[-1]
        return r

    def _handle_kong_prompt(self, resp: str) -> None:
        # Handle kong prompting for further authentication
        if self._kong_username_prompt in resp:
            resp = self._send_command(self._kong_username)
        if self._kong_password_prompt in resp:
            resp = self._send_command(self.password)
        return resp

# Not in use
class ISE(Appliance):
    def __init__(self, host, username, password, port):
        super().__init__(host, username, password, port)
        self._check_cmd = "show version"
        self._status_cmd = "show restore history"
        self._session_prompt = "press <Enter> to start a new one:"
        self._restore_history_fragment = "restore"
        self._term_len_cmd = "terminal length 0"
        self._restore_cmd_frame = [
            "restore",
            "",
            "repository",
            "",
            "encryption-key",
            "plain",
            "",
        ]
        self._restore_success = "Completing Restore...100% completed"
        self._restore_fail = "restore failed"

    def get_status(self) -> dict:
        # Tested and works
        resp = self._send_command(self._status_cmd)
        self.status = self._parse_show_restore_history(resp)
        return self.status

    def reset(self, backup_file, backup_repo, backup_key) -> tuple:
        self._restore_cmd_frame[1] = backup_file
        self._restore_cmd_frame[3] = backup_repo
        self._restore_cmd_frame[6] = backup_key
        restore_cmd = " ".join(self._restore_cmd_frame)
        self._send_command(restore_cmd)
        return self._wait_on_restore(
            self._restore_success, self._restore_fail, wait=300, interval=10
        )

    def _do_after_connect(self) -> None:
        """Tasks to do after connecting to ISE"""
        self._handle_session_prompt()
        self._send_command(self._term_len_cmd)

    def _handle_session_prompt(self) -> None:
        """Handle prompt to continue previous admin session"""
        post_login = self._read_shell(wait=2)
        if self._session_prompt in post_login:
            # Send \n to start new session
            # Ex. Enter session number to resume or press <Enter> to start a new one:
            self._send_command("")
        return

    def _parse_show_restore_history(self, s: str) -> dict:
        logger.debug("Input for parsing:")
        logger.debug(s)
        lines = s.split("\n")
        results = [line for line in lines if self._restore_history_fragment in line]
        parsed = {
            "last_restore": "None found",
            "restore_file": "None found",
            "status": "No restore history found",
            "host": self.host,
        }
        if results:
            result = results[-1]
            result = result.split()
            logger.debug("Parse result:")
            logger.debug(result)
            # Ex. ['Fri', 'Apr', '08', '19:54:08', 'UTC', '2022:', 'restore',
            # 'ise-with-users-ready4DNACb-CFG10-220325-1518.tar.gpg',
            # 'from', 'repository', 'ubuntu-ftp:', 'success']
            parsed = {
                "last_restore": f"{result[1]} {result[2]} {result[3]} {result[4]}",
                "restore_file": result[7],
                "status": f"Last restore: {result[-1]}",
                "host": self.host,
            }
        return parsed


class vManage(Appliance):
    def __init__(self, host, username, password, port):
        super().__init__(host, username, password, port)
        self._check_cmd = "show version"
        self._show_history = "show history"
        self._restore_cmd_stem = "request nms configuration-db restore path"
        self._screen_len_cmd = "screen-length 1000"
        self._cli_history_cmd = "history 1000"
        self._restore_log_cmd = "more /var/log/nms/neo4j-restore.log"
        self._restore_started = "Starting backup of configuration-db"
        self._restore_success = "Successfully restored database"
        self._restore_fail = "Failed to restore"
        self._status_cmd = self._show_history

    def get_status(self) -> dict:
        # Tested and works
        resp = self._send_command(self._status_cmd)
        default_result = {
            "last_restore": "None found",
            "restore_file": "None found",
            "status": "No restore history found",
            "host": self.host,
        }
        self.status = self._parse_show_history(resp, default_result)
        return self.status

    def reset(self, backup_path: str) -> tuple:
        # Tested and works
        cmd = f"{self._restore_cmd_stem} {backup_path}"
        self._send_command(cmd)
        return self._wait_on_restore(
            self._restore_success,
            self._restore_fail,
            wait=300,
            interval=8,
        )

    def _do_after_connect(self):
        # Send a \n to vManage first
        self._send_command("")
        # Set screen len higher
        self._send_command(self._screen_len_cmd)
        # We use CLI history to know when the last restore was
        # Set to largest value, 1000
        self._send_command(self._cli_history_cmd)

    def _parse_restore_log(self, s: str) -> dict:
        # Needs work, not in use
        lines = s.split("\n")
        # Sucessfully (sic)
        restore_success = [line for line in lines if s in line]
        if restore_success:
            entries_with_time = [line for line in lines if self.str_has_time(line)]
            restore_finished_time_entry = entries_with_time[-1]
            restore_finished_time = restore_finished_time_entry.split("org")[0].strip()
            parsed = {
                "last_restore": restore_finished_time,
                "restore_file": self._backup_path,
                "status": f"Last restore finished at {restore_finished_time}",
                "host": self.host,
            }
            return parsed

    def _parse_show_history(self, s: str, r: dict) -> dict:
        lines = s.split("\n")
        results = [line for line in lines if self._restore_cmd_stem in line]
        if results:
            result = results[-1]
            result = result.split(" -- ")
            result[-1] = result[-1].split()[-1]
            result[-1] = result[-1].split("/")[-1]
            # Ex. ['03-18 18:30:30', 'netdesign-advattached3.tar.gz']
            r["last_restore"] = result[0]
            r["restore_file"] = result[1]
            r["status"] = f"Last restore was at {result[0]}"
        return r

    def _verify_backup_file_path(self, path: str) -> bool:
        # Needs work, not in use
        logger.info("Verifying backup path...")
        logger.info(f"Looking for {path}...")
        self._send_command("vshell")
        ls_r = self._send_command("ls -l")
        self._send_command("exit")
        lines = ls_r.split("\n")
        lines = [line for line in lines if "tar.gz" in line]
        files = [line.split(" ")[-1] for line in lines]
        dir = f"/home/{self.username}"
        logger.debug(f"Using user dir: {dir}")
        for file in files:
            p = f"{dir}/{file}"
            logger.debug(r"")
            logger.debug(f"Checking path: {p}")
            if p == path:
                logger.info("Backup path exists.")
                return True
            logger.debug(f"Found path: {p}")
            logger.debug(f"Configured path: {path}")
        logger.info("Backup path doesn't exist.")
        return False
