from vmanage.api.authentication import Authentication
from vmanage.api.http_methods import HttpMethods
# from vmanage.data.parse_methods import ParseMethods
from abc import ABC


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


class vManage(ApplianceAPI):
    def __init__(self, host: str, username: str, password: str, port: str = "443"):
        super().__init__(host, username, password, port)
        self._session = Authentication(
            host=self.host, user=self.username, password=self.password
        ).login()
        self._base_url = f"https://{self.host}:{self.port}/dataservice/"

    def get_status(self) -> dict:
        pass

    def reset(self) -> tuple:
        pass

    def _get_back_up_list(self) -> list:
        url = f"{self._base_url}backup/list"
        r = HttpMethods(self._session, url).request("GET")
        # {'status_code': 200, 'status': 'ok', 'details': None, 'error': None,
        # 'json': {'backupList': []}, 'response': <Response [200]>}
        if r["status_code"] == 200:
            return r["json"]["backupList"]
        else:
            return r["error"]

    def _request_backup(self):
        url = f"{self._base_url}backup/export"
        payload = {}
        r = HttpMethods(self._session, url).request("POST", payload=payload)
        return r


if __name__ == "__main__":
    vm = vManage("192.168.1.1", "admin", "123!")
    r = vm._get_back_up_list()
    print(r)
    r = vm._request_backup()
    print(r)
