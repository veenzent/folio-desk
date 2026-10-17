# import datetime
import logging 
import random
import re
from typing import Any, Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extensions import uuid7

from app.core.config import (
    get_settings,
)
from app.core.exceptions import (
    EmailAlreadyRegisteredException,
    PhoneAlreadyRegisteredException,
    InternalServerErrorException,
    # PasswordMismatchException,
    PasswordRequirementsNotMetException,
    UserAlreadyRegisteredException,
    # TermsNotAcceptedException,
)
from app.core.security import get_user, get_user_by_phone, hasher
from app.models.users import Users # UserVerificationOTP
from app.schemas.auth_schemas import RegisterRequest, RegisterRequestResponse
# from app.tasks.email_tasks import mask_email, send_verification_email #TODO: Confirm email tasks requirements from Mr Ridwan before working on this.

logger = logging.getLogger(__name__)

settings = get_settings()
smtp_server = settings.smtp_server
email_username = settings.email_username
email_password = settings.email_password


async def create_new_user(user: RegisterRequest, db: AsyncSession) -> RegisterRequestResponse:
    """
    Creates a new client based on the provided RegisterRequest data

    Args:
        user (RegisterRequest): The signup request data
        db (AsyncSession): The async database session

    Raises:
        EmailAlreadyRegisteredException: If the email address is already
            registered
        PasswordMismatchException: If the password and confirm password do not
            match. Note: confirm password field would be available in future updates TODO: confirm password field.
        PasswordRequirementsNotMetException: If the password does not meet the
            requirements

    Returns:
        RegisterRequestResponse: The newly created user data
    """
    if not (password_check := validate_password(user.password))["is_valid"]:
        raise PasswordRequirementsNotMetException(details=password_check["results"])

    email_signup_type: bool = "@" in user.identifier

    if email_signup_type:
        if await get_user(
            db, user.identifier.lower()
        ):  # TODO: we would rely on DB's unique constraint at scale for performance 📝
            raise EmailAlreadyRegisteredException()
    else:
        if await get_user_by_phone(db, user.identifier):
            raise PhoneAlreadyRegisteredException()

    try:
        new_user = Users(
            id=uuid7(),
            email_address=user.identifier if "@" in user.identifier else None,
            phone_number=user.identifier if "@" not in user.identifier else None,
            password_hash=hasher.hash(user.password),
        )

        # generate and store hashed OTP in database
        # new_otp = UserVerificationOTP(
        #     id=uuid7(),
        #     user_id=new_user.id,
        #     otp_hash=hasher.hash(otp := generate_otp()),
        #     purpose="signup verification",
        #     expires_at=datetime.datetime.now(datetime.timezone.utc)
        #     + datetime.timedelta(minutes=settings.signup_otp_expiration_minutes),
        # )

        db.add_all([new_user])
        # db.add_all([new_user, new_otp])
        await db.commit()
        await db.refresh(new_user)

    except IntegrityError:
        await db.rollback()
        raise UserAlreadyRegisteredException()
    except Exception:
        await db.rollback()
        logger.exception("[USER SIGNUP]: Failed to create new user")
        raise InternalServerErrorException()

    # TODO: Confirm email requirements / credentials from Mr Ridwan before working on this.
    # initiate background task to send OTP email for verification
    # masked_email = mask_email(user.identifier) if email_signup_type else "N/A"   # TODO: setup logic for phone number verification
    # logger.info(f"[USER SIGNUP]: Sending verification email to user ID={masked_email}")

    # send_verification_email.delay(
    #     user_id=str(new_user.id),
    #     otp=otp,
    #     expiry_minutes=settings.signup_otp_expiration_minutes,
    #     year=datetime.datetime.now().year,
    # )

    return RegisterRequestResponse(
        message="User created successfully"
    )


def validate_password(password: str) -> Dict[str, Any]:
    """
    Checks a password against common security requirements.

    Requirements:
    1. Minimum 8 characters long.
    2. Contains at least one uppercase letter.
    3. Contains at least one lowercase letter.
    4. Contains at least one digit (number).
    5. Contains at least one special character.

    Args:
        password: The string to be validated.

    Returns:
        A dictionary containing the overall validity status and the status
        of each individual check.
    """
    # set of common special characters for this validation
    SPECIAL_CHARACTERS = r"[!@#$%^&*()_+=\-[\]{};':\"\\|,.<>/?`~]"

    # Perform individual checks
    checks = {
        "min_length_8": {
            "passed": len(password) >= 8,
            "description": "8 Characters (Minimum)",
        },
        "has_uppercase": {
            "passed": any(c.isupper() for c in password),
            "description": "Uppercase Letter",
        },
        "has_lowercase": {
            "passed": any(c.islower() for c in password),
            "description": "Lowercase Letter",
        },
        "has_number": {
            "passed": any(c.isdigit() for c in password),
            "description": "Number",
        },
        # Use regex to check for any special character in the defined set
        "has_special_char": {
            "passed": bool(re.search(SPECIAL_CHARACTERS, password)),
            "description": "Special Character",
        },
    }

    # Determine overall validity
    all_passed = all(check["passed"] for check in checks.values())

    return {"is_valid": all_passed, "results": checks}


def generate_otp(length: int = 6) -> str:
    """Generate a 6-digit numeric OTP"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])
