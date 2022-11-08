from abc import ABC
import logging
from datetime import datetime
import requests
import json


class ApplianceAPI(ABC):
    def __init__(self, host: str, username: str, password: str, port: str):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    def get_status(self) -> dict:
        pass

    def reset(self) -> tuple:
        pass


requests.packages.urllib3.disable_warnings()


class DNAC(ApplianceAPI):
    def __init__(self, host: str, username: str, password: str, port: str = 443, verify: bool = False):
        super().__init__(host, username, password, port)
        self._logger = logging.getLogger("civlab_api")
        self._base_url = f"https://{host}:{port}"
        self.verify = verify
        self._token = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._auth_resp = self._auth()

    def reset(self) -> dict:
        pass

    def _auth(self) -> dict:
        path = f"{self._base_url}/dna/system/api/v1/auth/token"
        self._logger.info(f"POST {path}")
        resp = requests.post(
            path,
            auth=(self.username, self.password),
            headers=self._headers,
            verify=self.verify,
        )
        resp.raise_for_status()
        r_json = resp.json()
        self._token = r_json.get("Token")
        self._headers["X-Auth-Token"] = self._token
        return r_json

    def _request(
        self, method: str, path: str, params: dict = None, body: dict = None
    ) -> dict:
        path = f"{self._base_url}{path}"
        method = str(method).lower()
        req = getattr(requests, method)
        self._logger.info(f"{method.upper()} {path}")
        resp = req(
            path, headers=self._headers, verify=self.verify, params=params, json=body
        )
        self._logger.debug(f"Status code: {resp.status_code}")
        self._logger.debug(resp.text)
        resp.raise_for_status()
        return resp.json()

    def _get_restore_history(self) -> list:
        path = "/api/system/v1/maglev/restore/history"
        r = self._request("get", path)
        r["response"] = sorted(
            r["response"], key=lambda k: k["end_timestamp"]
        )
        return r["response"]
    
    def get_status(self) -> dict:
        restore_history = self._get_restore_history()[-1]
        last_restore = restore_history.get("end_timestamp")
        last_restore = datetime.fromtimestamp(last_restore).isoformat(sep=" ", timespec='minutes')
        result = {
            "last_restore": last_restore,
            "restore_id": restore_history.get("description"),
            "status": restore_history.get("status"),
            "host": self.host,
        }
        return result


if __name__ == "__main__":
    vm = DNAC("10.1.1.1", "admin", "12345!")
    r = vm._get_restore_history()
    r = r[-1]
    with open("dnac_output", "w") as fh:
        fh.write(json.dumps(r, indent=4))
    print(json.dumps(r, indent=4))
    r = vm.get_status()
    print(r)