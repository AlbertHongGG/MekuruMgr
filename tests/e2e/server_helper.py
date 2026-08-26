import json
from fastapi.testclient import TestClient
from .logger import TestOutputLogger

class ServerTestHelper:
    def __init__(self, app, logger: TestOutputLogger):
        self.client = TestClient(app)
        self.logger = logger

    def get(self, step_title: str, url: str, params: dict = None) -> dict | list | None:
        req_info = f"GET {url}"
        if params:
            req_info += f" params={params}"
            
        response = self.client.get(url, params=params)
        
        try:
            data = response.json()
            output = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            data = None
            output = f"Status: {response.status_code}\nContent:\n{response.text}"

        self.logger.log_step(step_title, req_info, output)
        return data

    def post(self, step_title: str, url: str, json_data: dict = None) -> dict | list | None:
        req_info = f"POST {url} json={json_data}"
        response = self.client.post(url, json=json_data)
        
        try:
            data = response.json()
            output = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            data = None
            output = f"Status: {response.status_code}\nContent:\n{response.text}"

        self.logger.log_step(step_title, req_info, output)
        return data

    def log_message(self, message: str):
        self.logger.log_message(message)
