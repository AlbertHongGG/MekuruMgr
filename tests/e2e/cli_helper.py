from typer.testing import CliRunner
from .logger import TestOutputLogger
import typer

class CliTestHelper:
    def __init__(self, app: typer.Typer, logger: TestOutputLogger):
        self.app = app
        self.runner = CliRunner()
        self.logger = logger

    def invoke(self, step_title: str, args_list: list) -> str:
        cmd_str = f"cli {' '.join(args_list)}"
        result = self.runner.invoke(self.app, args_list)
        
        output = result.stdout
        if result.exception and not isinstance(result.exception, SystemExit):
            output += f"\n[EXCEPTION]\n{str(result.exception)}"
            
        self.logger.log_step(step_title, cmd_str, output)
        return output

    def log_message(self, message: str):
        self.logger.log_message(message)
