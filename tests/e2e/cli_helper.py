from typer.testing import CliRunner
from .logger import TestOutputLogger

class CliTestHelper:
    def __init__(self, app):
        self.app = app
        self.runner = CliRunner()
        self.logger = None

    def set_target(self, target_name: str):
        """Set the target name (e.g. 'webtoon') to initialize logging."""
        self.logger = TestOutputLogger(mode="cli", name=target_name)

    def invoke(self, step_title: str, args_list: list) -> str:
        if not self.logger:
            raise RuntimeError("Must call set_target() before invoke()")
            
        cmd_str = f"cli {' '.join(args_list)}"
        result = self.runner.invoke(self.app, args_list)
        
        output = result.stdout
        if result.exception and not isinstance(result.exception, SystemExit):
            output += f"\n[EXCEPTION]\n{str(result.exception)}"
            
        self.logger.log_step(step_title, cmd_str, output)
        return output

    def log_message(self, message: str):
        if self.logger:
            self.logger.log_message(message)
