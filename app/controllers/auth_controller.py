import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from app.config import get_auth_settings
from app.schemas.auth_schemas import (
    AuthTokenResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    UserResponse,
)
from app.security import get_current_user
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_verification_token,
    get_user_by_email,
    register_user,
    verify_email_token,
)
from app.services.email_service import send_verification_email

logger = logging.getLogger(__name__)
router = APIRouter()


def send_verification_link(email: str, token: str) -> None:
    settings = get_auth_settings()
    verification_url = (
        f"{settings['app_base_url']}/auth/verify-email"
        f"?token={quote(token, safe='')}"
    )
    send_verification_email(email, verification_url)


@router.post(
    "/auth/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(request: RegisterRequest):
    try:
        _, token = register_user(
            name=request.name,
            email=str(request.email),
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    try:
        send_verification_link(str(request.email), token)
    except Exception as exc:
        logger.exception("Could not send verification email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Your account was created but the verification email "
                "could not be sent. Please try the resend endpoint."
            ),
        ) from exc

    return MessageResponse(
        message="Account created. Check your email to verify your address."
    )


@router.get(
    "/auth/verify-email",
    response_class=HTMLResponse,
    tags=["Authentication"],
)
def verify_email(token: str):
    if not token or len(token) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link.",
        )

    if not verify_email_token(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification link is invalid or has expired.",
        )

    return HTMLResponse("""
        <!doctype html>
        <html>
          <head><title>Email verified</title></head>
          <body>
            <h1>Email verified successfully!</h1>
            <p>You can now return to the application and log in.</p>
          </body>
        </html>
        """)


@router.post(
    "/auth/resend-verification",
    response_model=MessageResponse,
    tags=["Authentication"],
)
def resend_verification(request: ResendVerificationRequest):
    user = get_user_by_email(str(request.email))

    # Avoid revealing whether an email belongs to an account.
    if user is None or user["is_email_verified"]:
        return MessageResponse(
            message=(
                "If an unverified account exists for this email, "
                "a verification email will be sent."
            )
        )

    token = create_verification_token(user["id"])

    try:
        send_verification_link(user["email"], token)
    except Exception as exc:
        logger.exception("Could not resend verification email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The verification email could not be sent. Try again later.",
        ) from exc

    return MessageResponse(
        message=(
            "If an unverified account exists for this email, "
            "a verification email will be sent."
        )
    )


@router.post(
    "/auth/login",
    response_model=AuthTokenResponse,
    tags=["Authentication"],
)
def login(request: LoginRequest):
    user, error = authenticate_user(
        email=str(request.email),
        password=request.password,
    )

    if error == "email_not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in.",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(user["id"])

    return AuthTokenResponse(
        access_token=access_token,
        expires_in=expires_in,
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["Authentication"],
)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        is_email_verified=bool(current_user["is_email_verified"]),
    )
