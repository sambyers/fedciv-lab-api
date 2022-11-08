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
