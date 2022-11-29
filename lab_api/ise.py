import logging
from ciscoisesdk import IdentityServicesEngineAPI
from ciscoisesdk.exceptions import ciscoisesdkException, ApiError
from .appliance import ApplianceAPI


class ISE(ApplianceAPI):
    def __init__(
        self, host: str, username: str, password: str, version: str, port: str = "443"
    ):
        super().__init__(host, username, password, port)
        self._base_url = f"https://{self.host}:{self.port}"
        self._api = IdentityServicesEngineAPI(
            username=self.username,
            password=self.password,
            base_url=self._base_url,
            version=version,
            verify=False,
        )
        self._logger = logging.getLogger("civlab_api")

    def get_status(self) -> dict:
        result = {
            "last_restore": "",
            "restore_file": "",
            "status": "",
            "host": self.host,
        }
        try:
            r = self._api.backup_and_restore.get_last_status()
        except (ciscoisesdkException, ApiError) as e:
            result["status"] = str(e)
            return result
        resp = r.response
        self._logger.debug(f"ISE response: {r.status_code} {resp}")
        if r.status_code == 200:
            result["last_restore"] = resp.response.startDate
            result["restore_file"] = resp.response.name
            result["status"] = f"{resp.response.action} {resp.response.status}"
        else:
            result["status"] = resp
        return result

    def reset(self, backup_file: str, backup_repo: str, backup_key: str) -> tuple:
        if not self._check_backup_file(backup_file, backup_repo):
            return False, "Backup file doesn't exist."
        try:
            r = self._api.backup_and_restore.restore(
                backup_encryption_key=backup_key,
                repository_name=backup_repo,
                restore_file=backup_file,
                restore_include_adeos="false",
            )
        except (ciscoisesdkException, ApiError) as e:
            return False, str(e)
        resp = r.response
        self._logger.debug(f"ISE response: {r.status_code} {resp}")
        if r.status_code == 202:
            return True, resp.response.message
        else:
            return False, resp.message

    def _check_backup_file(self, file, repo) -> bool:
        r = self._api.repository.get_files(repo)
        resp = r.response.response
        if file in resp:
            return True
        else:
            return False

    def update_repo_pass(self, name, password) -> tuple:
        """Update the ISE repo password"""
        repo = self.get_repo(name)
        self._logger.info(f"Updating password for ISE repo {repo.name}")
        self._logger.debug(f"Updating repo: {repo}")
        try:
            r = self._api.repository.update_repository(
                repo.name,
                password=password,
                path=repo.path,
                protocol=repo.protocol,
                server_name=repo.serverName,
                user_name=repo.userName,
                # name=repo.name,
            )
        except (ciscoisesdkException, ApiError) as e:
            return False, str(e)
        resp = r.response
        self._logger.debug(f"ISE response: {r.status_code} {resp}")
        if r.status_code == 200:
            return True, resp.success.message
        else:
            return False, resp.error.message

    def get_repo(self, name) -> dict:
        self._logger.info(f"Getting ISE repo {name}...")
        r = self._api.repository.get_repository(name)
        self._logger.debug(f"ISE response: {r.status_code} {r.response}")
        return r.response.response
