from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details=None):
        super().__init__(
            status_code=status_code,
            detail={"error_code": error_code, "message": message, "details": details},
        )


class InternalServerErrorException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
        )


class EmailAlreadyRegisteredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMAIL_ALREADY_REGISTERED",
            message="Email address already registered",
        )


class EmailRequiredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMAIL_REQUIRED",
            message="Email address is required",
        )


class InvalidEmailException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INCORRECT_EMAIL_ADDRESS",
            message="Incorrect email address",
        )


class PhoneAlreadyRegisteredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PHONE_ALREADY_REGISTERED",
            message="Phone number already registered",
        )


class UserAlreadyRegisteredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="USER_ALREADY_REGISTERED",
            message="User is already registered",
        )


class PasswordMismatchException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PASSWORD_MISMATCH",
            message="Password and confirm password do not match",
        )


class PasswordRequirementsNotMetException(CustomHTTPException):
    def __init__(self, details: dict = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PASSWORD_REQUIREMENTS_NOT_MET",
            message="Password does not meet requirements",
            details=details,
        )


class TermsNotAcceptedException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="TERMS_AND_CONDITIONS_NOT_ACCEPTED",
            message="Terms and conditions must be accepted",
        )


class UserNotFoundException(CustomHTTPException):
    def __init__(self, user_id: int = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
            message="User not found",
            details={"user_id": user_id} if user_id else None,
        )


class InvalidCredentialsException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            message="Invalid username or password",
        )


class TokenExpiredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED",
            message="Token has expired",
        )


class InvalidRoleException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INVALID_ROLE",
            message="You do not have permission to perform this action",
        )
