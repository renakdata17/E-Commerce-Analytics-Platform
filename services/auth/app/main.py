"""OAuth2-compatible token endpoint for MerchantUser accounts."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from ecommerce_platform.auth.jwt import issue_access_token
from ecommerce_platform.db.models import MerchantUser
from ecommerce_platform.settings import settings
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select

from .db import SessionLocal

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _bootstrap_default_merchant() -> None:
    email = settings.ADMIN_BOOTSTRAP_EMAIL
    password = settings.ADMIN_BOOTSTRAP_PASSWORD
    if not email or not password:
        return
    db = SessionLocal()
    try:
        if db.scalar(select(MerchantUser).where(MerchantUser.email == email)):
            return
        hashed = PWD_CONTEXT.hash(password)
        db.add(MerchantUser(email=email, hashed_password=hashed, analyst=True))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _bootstrap_default_merchant)
    yield


app = FastAPI(
    title="Acme Outfitters Auth Service",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/oauth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user = db.scalar(select(MerchantUser).where(MerchantUser.email == form_data.username))
        if user is None or user.disabled:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not PWD_CONTEXT.verify(form_data.password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = issue_access_token(
            subject=user.id,
            secret=settings.JWT_SECRET,
            issuer=settings.JWT_ISSUER,
            algorithm=settings.JWT_ALG,
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            email=user.email,
            analyst=user.is_analyst,
            scopes=("catalog:admin",),
        )
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "auth-ok"}
