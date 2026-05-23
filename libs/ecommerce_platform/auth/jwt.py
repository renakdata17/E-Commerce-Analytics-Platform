from __future__ import annotations

import datetime as dt

from jose import JWTError, jwt
from pydantic import BaseModel


class JWTPayload(BaseModel):
    sub: str
    email: str | None = None
    scopes: tuple[str, ...] = ()
    analyst: bool = False


def issue_access_token(
    *,
    subject: str,
    secret: str,
    issuer: str,
    algorithm: str,
    minutes: int,
    email: str | None = None,
    analyst: bool = False,
    scopes: tuple[str, ...] = (),
) -> str:
    """Mint a bearer token usable by storefront + internal dashboards."""

    now = dt.datetime.now(tz=dt.UTC)
    payload = {
        "sub": subject,
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=minutes)).timestamp()),
        "email": email,
        "scopes": list(scopes),
        "analyst": analyst,
    }
    return jwt.encode(payload, secret, algorithm)


def decode_token(token: str, *, secret: str, algorithms: list[str], issuer: str) -> JWTPayload:
    try:
        data = jwt.decode(
            token,
            secret,
            algorithms=algorithms,
            issuer=issuer,
            options={"require": ["exp", "iss", "sub"]},
        )
    except JWTError as exc:
        raise ValueError("invalid token") from exc

    return JWTPayload(
        sub=str(data["sub"]),
        email=data.get("email"),
        scopes=tuple(str(s) for s in data.get("scopes", []) or ()),
        analyst=bool(data.get("analyst", False)),
    )
