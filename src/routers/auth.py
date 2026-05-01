from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db import get_db
from src.models.user import User
from src.schemas.user import SignupRequest, LoginRequest, TokenResponse, MonitoringTokenRequest, VALID_ROLES
from src.core.auth import hash_password, verify_password, create_token, MONITORING_API_KEY, decode_token
from src.core.dependencies import bearer, get_current_user
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {sorted(VALID_ROLES)}")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        institution_id=body.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token}


@router.post("/monitoring-token", response_model=TokenResponse)
def monitoring_token(
    body: MonitoringTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    # Validate the standard JWT first
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("scope") == "monitoring":
        raise HTTPException(status_code=400, detail="Already a monitoring token")

    role = payload.get("role")
    if role != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Only monitoring_officer can obtain monitoring tokens")

    if body.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user_id = payload.get("sub")
    scoped = create_token(
        {"sub": user_id, "role": role, "scope": "monitoring"},
        expires_hours=1,
    )
    return {"access_token": scoped}
