import os
import requests

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")

ALGORITHMS = ["RS256"]


def verify_auth0_token(token: str) -> dict:
    try:
        # -----------------------------------------
        # 1. Get Auth0 public keys
        # -----------------------------------------

        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

        jwks_response = requests.get(jwks_url, timeout=10)

        if jwks_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not get Auth0 public keys"
            )

        jwks = jwks_response.json()

        # -----------------------------------------
        # 2. Read token header
        # -----------------------------------------

        unverified_header = jwt.get_unverified_header(token)

        rsa_key = None

        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if rsa_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth0 token"
            )

        # -----------------------------------------
        # 3. Verify JWT token
        # -----------------------------------------

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience="https://smart-ecommerce-api",
            issuer=f"https://{AUTH0_DOMAIN}/"
        )

        # -----------------------------------------
        # 4. Get user information from Auth0
        # -----------------------------------------

        userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"

        userinfo_response = requests.get(
            userinfo_url,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not get user information from Auth0"
            )

        userinfo = userinfo_response.json()

        # -----------------------------------------
        # 5. Add user information to payload
        # -----------------------------------------

        payload["email"] = userinfo.get("email")
        payload["name"] = (
            userinfo.get("name")
            or userinfo.get("nickname")
            or "User"
        )

        # Auth0 user ID
        payload["sub"] = userinfo.get("sub", payload.get("sub"))

        return payload

    except HTTPException:
        raise

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Auth0 token"
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not connect to Auth0"
        )

    except Exception as e:
        print("Auth0 verification error:", str(e))

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )