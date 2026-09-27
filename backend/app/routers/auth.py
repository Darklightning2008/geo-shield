import os
import hashlib
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Depends

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])

# Specialized Admin Credentials for Emergency Operations Center (EOC / IMD / NDMA)
ADMIN_USERS = {
    "admin@geoshield.gov.in": {
        "password_hash": hashlib.sha256("Admin@NDMA2026".encode("utf-8")).hexdigest(),
        "name": "National EOC Officer",
        "agency": "NDMA / IMD Disaster Warning Directorate",
        "clearance": "Level-1 Emergency Operations Administrator"
    },
    "admin@imd.gov.in": {
        "password_hash": hashlib.sha256("Admin@123".encode("utf-8")).hexdigest(),
        "name": "IMD Regional Met Superintendent",
        "agency": "India Meteorological Department",
        "clearance": "Level-1 Meteorological Administrator"
    }
}

class LoginRequest(BaseModel):
    email: str
    password: str

class AdminProfile(BaseModel):
    email: str
    name: str
    agency: str
    clearance: str

class LoginResponse(BaseModel):
    authenticated: bool
    role: str
    token: str
    profile: AdminProfile

@router.post("/login", response_model=LoginResponse)
async def admin_login(creds: LoginRequest):
    """
    Authenticates specialized disaster administration personnel (NDMA / IMD / EOC).
    Grants access to contingency metrics (POD/FAR/CSI), sensor provenance audits,
    and official OASIS CAP v1.2 machine-readable feeds.
    """
    clean_email = creds.email.strip().lower()
    user_info = ADMIN_USERS.get(clean_email)

    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Specialized administrator email unrecognized. Only authorized EOC/IMD personnel may enter Admin mode."
        )

    provided_hash = hashlib.sha256(creds.password.strip().encode("utf-8")).hexdigest()
    if provided_hash != user_info["password_hash"]:
        raise HTTPException(
            status_code=401,
            detail="Incorrect administrator password for this specialized account."
        )

    # Issue deterministic session token
    token = f"eoc-auth-{hashlib.sha256((clean_email + 'geoshield-secret-salt-2026').encode('utf-8')).hexdigest()[:32]}"

    return LoginResponse(
        authenticated=True,
        role="admin",
        token=token,
        profile=AdminProfile(
            email=clean_email,
            name=user_info["name"],
            agency=user_info["agency"],
            clearance=user_info["clearance"]
        )
    )

@router.get("/status")
async def verify_auth_status(authorization: Optional[str] = Header(None)):
    """Verifies token validity for current session."""
    if not authorization:
        return {"authenticated": False, "role": "citizen"}
    
    token = authorization.replace("Bearer ", "").strip()
    if token.startswith("eoc-auth-"):
        return {"authenticated": True, "role": "admin"}
    return {"authenticated": False, "role": "citizen"}
