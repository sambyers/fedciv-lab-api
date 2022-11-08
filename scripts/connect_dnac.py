# Testing connectivity to DNAC
import os
import socket
import time
import paramiko
import yaml


def get_appliances():
    path = os.getenv("CIVLAB_APPLIANCE_DATA")
    with open(path, "r") as stream:
        data = yaml.load(stream, Loader=yaml.Loader)
    return data


class Appliance:
    def __init__(self, ip: str, username: str, password: str, port: int):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
        self.shell = None

    def connect(self) -> bool:
        if not self._check_connection():
            self._connect_ssh()
            self.shell = self.ssh.invoke_shell()
            return True

    def _connect_ssh(self) -> bool:
        print(f"Connecting to {self.ip}:{self.port}")
        self.ssh.connect(self.ip, self.port, self.username, self.password)
        self.connected = True
        return True

    def _check_connection(self) -> bool:
        """
        This will check if the connection is still availlable.

        Return (bool) : True if it's still alive, False otherwise.
        """
        try:
            self.ssh.exec_command("\n", timeout=5)
            return True
        except Exception as e:
            print(f"Connection lost: {e}")
            return False

    def _send_command(self, cmd: str) -> str:
        try:
            print(f"Sending command: {cmd}")
            cmd = cmd + "\n"
            sent_bytes = self.shell.send(cmd)
            assert sent_bytes == len(cmd.encode("utf-8"))
            time.sleep(4)
            # Tested the largest return data is 11587 bytes in utf-8
            resp = self.shell.recv(20000).decode("utf-8")
            print("Response:")
            print(resp)
            return resp
        except (
            paramiko.BadHostKeyException,
            paramiko.AuthenticationException,
            paramiko.SSHException,
            socket.error,
        ) as error:
            return error


class DNACDevice(Appliance):
    def __init__(self, ip, username, password, port):
        super().__init__(ip, username, password, port)

    def reset(self, backup_id: str):
        restore_cmd = "maglev restore apply " + backup_id
        return self._send_command(restore_cmd)

    def get_status(self) -> list:
        cmd = "maglev restore history"
        resp = self._send_command(cmd)
        if "password for 'admin'" in resp:
            resp = self._send_command(self.password)
        elif "[administration] username for" in resp:
            resp = self._send_command("admin")
        else:
            return self._parse_restore_hist(resp)

    def _parse_restore_hist(self, s: str) -> list:
        lines = s.split("\n")
        results = []
        for line in lines:
            if "RESTORE.FINALIZE_RESTORE" in line:
                results.append(line)
        result = results.pop()
        result = result.split()
        # ['2022-03-22', '21:23:09', 'ee84abae-a11b-45c6-94c3-d578cfe888f6',
        # 'RESTORE.FINALIZE_RESTORE', 'SUCCESS']
        return result


def main():
    appliances = get_appliances()
    dnac_info = appliances.get("dnac")
    dnac = DNACDevice(
        dnac_info["ip"], dnac_info["username"], dnac_info["password"], dnac_info["port"]
    )
    dnac.connect()
    dnac_status = dnac.get_status()
    print(dnac_status)


if __name__ == "__main__":
    main()
