class AppBaseError(Exception):
    """Base exception for all application errors."""
    pass

class NetworkError(AppBaseError):
    """Raised when HTTP request fails (connection error, timeout, 5xx)."""
    pass

class ApiLogicError(AppBaseError):
    """Raised when the API returns 200 OK but the business logic code is not success."""
    def __init__(self, message: str, code: int):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message

class SignError(AppBaseError):
    """Raised when signature generation fails."""
    pass
