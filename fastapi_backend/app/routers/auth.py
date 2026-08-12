from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)

from app.core.auth0 import verify_auth0_token


# =========================================================
# Router Configuration
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


# =========================================================
# Register API
# =========================================================

@router.post("/register")
def register(
    name: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="customer"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }


# =========================================================
# Login API
# =========================================================

@router.post("/login")
def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    # Find user
    user = db.query(User).filter(
        User.email == email
    ).first()

    # Verify credentials
    if not user or not verify_password(
        password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# =========================================================
# Refresh Token API
# =========================================================

@router.post("/refresh")
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = decode_token(token)

        # Make sure this is a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        user_id = int(payload.get("sub"))

        # Create new access token
        new_access_token = create_access_token(user_id)

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )


# =========================================================
# Current User API
# =========================================================

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


# =========================================================
# Auth0 Login API
# =========================================================

@router.post("/auth0")
def auth0_login(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Get Auth0 token
    token = credentials.credentials

    # Verify Auth0 token
    payload = verify_auth0_token(token)

    # Get user information from Auth0
    auth0_id = payload.get("sub")
    email = payload.get("email")
    name = (
        payload.get("name")
        or payload.get("nickname")
        or "User"
    )

    # Make sure Auth0 ID exists
    if not auth0_id:
        raise HTTPException(
            status_code=400,
            detail="Auth0 user ID not provided"
        )

    # =====================================================
    # Facebook may not provide an email.
    # Create a unique internal email using Auth0 ID.
    # =====================================================

    if not email:
        safe_auth0_id = (
            auth0_id
            .replace("|", "_")
            .replace(":", "_")
            .replace("/", "_")
            .replace(" ", "_")
        )

        email = f"{safe_auth0_id}@auth.local"

    # Check if user already exists
    user = db.query(User).filter(
        User.email == email
    ).first()

    # Create local user if not already present
    if not user:
        user = User(
            name=name,
            email=email,
            password=hash_password(auth0_id),
            role="customer"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # Create our application's JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "message": "Auth0 authentication successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.id,
            "auth0_id": auth0_id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }