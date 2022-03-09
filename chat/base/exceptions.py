class BaseCustomException(Exception):
    default_message = "Exception occured"

    def __init__(self, message=None, errors=None):
        super().__init__(str(message), errors)
        self.message = str(message) if message else self.default_message


class PermissionDenied(BaseCustomException):
    status = 403
    default_message = "You don't have permission to perform this action"


class NotFound(BaseCustomException):
    status = 404
    default_message = 'Object not found!'


class ValidationError(BaseCustomException):
    status = 400
    default_message = "Validation error"
