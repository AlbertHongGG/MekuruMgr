class AppBaseError(Exception):
    """Base exception for the entire application."""
    pass

class NetworkError(AppBaseError):
    """Raised when a network-level error occurs (e.g. timeout, connection error)."""
    pass

class ApiLogicError(AppBaseError):
    """Raised when the API returns an error code (code != 200)."""
    def __init__(self, message: str, code: int):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message

class AuthError(ApiLogicError):
    """Raised for authentication or signature errors."""
    pass

class RateLimitError(ApiLogicError):
    """Raised when API rate limit is exceeded."""
    pass
