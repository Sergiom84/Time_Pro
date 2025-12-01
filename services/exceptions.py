class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass

class ResourceNotFound(ServiceError):
    """Raised when a requested resource is not found."""
    pass

class ResourceAlreadyExists(ServiceError):
    """Raised when trying to create a resource that already exists."""
    pass

class ValidationError(ServiceError):
    """Raised when validation fails (e.g. empty fields)."""
    pass

class OperationNotAllowed(ServiceError):
    """Raised when an operation is not allowed (e.g. deleting a category in use)."""
    pass
