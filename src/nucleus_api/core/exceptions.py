class NucleusAPIException(Exception):
    """Base class for all exceptions in the Nucleus API."""

    def __init__(self, message: str):
        super().__init__(message)
        self.detail = message

class NotFoundException(NucleusAPIException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)

class ConflictException(NucleusAPIException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)

class UnauthorizedException(NucleusAPIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)