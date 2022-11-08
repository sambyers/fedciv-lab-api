import logging
import requests
from .appliance import ApplianceAPI


requests.packages.urllib3.disable_warnings()


class DNAC(ApplianceAPI):
    def __init__(self, host: str, username: str, password: str, port: str = 443, verify: bool = False):
        super().__init__(host, username, password, port)
        self._logger = logging.getLogger("civlab_api")
        self.verify = verify
        self._token = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._auth_resp = self._auth()

    def get_status(self) -> dict:
        pass

    def reset(self) -> dict:
        pass

    def _auth(self) -> dict:
        path = f"{self.host}/dna/system/api/v1/auth/token"
        self._logger.info(f"POST {path}")
        resp = requests.post(
            path,
            auth=(self.username, self.password),
            headers=self.headers,
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
        method = str(method).lower()
        req = getattr(requests, method)
        self._logger.info(f"{method.upper()} {path}")
        resp = req(
            path, headers=self.headers, verify=self.verify, params=params, json=body
        )
        self._logger.debug(f"Status code: {resp.status_code}")
        self._logger.debug(resp.text)
        resp.raise_for_status()
        return resp.json()

    def _get_backup_history(self) -> dict:
        path = f"{self.host}/api/system/v1/maglev/backup"
        return self._request("get", path)


if __name__ == "__main__":
    vm = DNAC("192.133.187.27", "admin", "FEDciv123!")
    r = vm._get_backup_history()
    print(r)
