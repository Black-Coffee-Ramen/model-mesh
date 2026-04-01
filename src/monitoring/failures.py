from enum import Enum
from litellm import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
    APIConnectionError,
    InternalServerError
)

class ErrorCategory(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error" # API errors, service unavailable
    INVALID_REQUEST = "invalid_request" # Auth, Bad Request
    UNKNOWN = "unknown"

def classify_error(error: Exception) -> ErrorCategory:
    """
    Classify a LiteLLM error into a standard category for monitoring.
    """
    err_str = str(error).lower()
    
    if isinstance(error, RateLimitError):
        return ErrorCategory.RATE_LIMIT
    
    if isinstance(error, Timeout) or "timeout" in err_str:
        return ErrorCategory.TIMEOUT
    
    if isinstance(error, (ServiceUnavailableError, InternalServerError, APIConnectionError)):
        return ErrorCategory.PROVIDER_ERROR
    
    if isinstance(error, (AuthenticationError, BadRequestError)):
        return ErrorCategory.INVALID_REQUEST
        
    return ErrorCategory.UNKNOWN
