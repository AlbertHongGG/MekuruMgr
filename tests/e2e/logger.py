import os

current_test_mode = "unknown"

class TestOutputLogger:
    def __init__(self, mode: str, name: str):
        """
        mode: e.g., 'cli' or 'server'
        name: e.g., 'webtoon', 'library'
        """
        global current_test_mode
        current_test_mode = mode
        
        self.output_dir = os.path.join("test_outputs", mode, name)
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, "flow_output.txt")
        
        # 每次初始化時清空檔案
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(f"=== E2E Test Output ({mode.upper()}) - {name} ===\n\n")
            
    def log_step(self, title: str, request_info: str, output: str):
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(f"========================================\n")
            f.write(f"=== {title}\n")
            f.write(f"=== REQ/CMD: {request_info}\n")
            f.write(f"========================================\n")
            if not output:
                f.write("(No Output)\n\n")
            else:
                f.write(f"{output}\n\n")

    def log_message(self, message: str):
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(f"--- {message} ---\n\n")
