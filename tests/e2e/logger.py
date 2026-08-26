import os

class TestOutputLogger:
    def __init__(self, file_path: str, title: str):
        """
        file_path: The absolute or relative path to the log file (e.g., test_outputs/cli/webtoon/comic.log)
        title: Title to write at the beginning of the log.
        """
        self.output_file = file_path
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        is_new = not os.path.exists(self.output_file)
        
        with open(self.output_file, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"=== {title} ===\n\n")
            
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
