from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import hashlib
import logging
import re

from backend.utils.auth import create_token, verify_token
from backend.utils.email import generate_otp, store_otp, verify_otp, send_otp_email
from backend.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ------------------------------------------------------------
# Request Models
# ------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    """
    Professional profile for medical coders, billing specialists,
    insurance reviewers, and healthcare admin staff.
    All fields are optional — only provided fields will be updated.
    """
    # Personal Info
    name:         Optional[str] = None   # Full name
    phone:        Optional[str] = None   # Contact number
    age:          Optional[str] = None   # Age

    # Professional Info
    organization: Optional[str] = None  # Hospital / clinic / insurance company / billing firm
    department:   Optional[str] = None  # e.g. "Medical Coding", "Claims & Billing", "Insurance Review"
    role:         Optional[str] = None  # e.g. "Medical Coder", "Billing Specialist", "Claims Analyst"
    work_email:   Optional[str] = None  # Work email (may differ from login email)

    # Device
    fcmToken:     Optional[str] = None  # Push notification token


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _build_user_response(user_dict) -> dict:
    """Single place that defines the user object shape returned to the client."""
    return {
        "id":           str(user_dict["id"]),
        "name":         user_dict["name"] or "",
        "email":        user_dict["email"] or "",
        "phone":        user_dict["phone"] or "",
        "age":          user_dict["age"] or "",
        # Professional fields
        "organization": user_dict["organization"] or "",
        "department":   user_dict["department"] or "",
        "role":         user_dict["role"] or "",
        "work_email":   user_dict["work_email"] or "",
    }


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

def is_valid_email(email: str) -> bool:
    regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(regex, email))


@router.post("/register")
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if not body.email or not body.email.strip():
        raise HTTPException(status_code=400, detail="Email cannot be empty")
    if not body.password or not body.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    if len(body.name) > 255:
        raise HTTPException(status_code=400, detail="Name must be 255 characters or less")
    if len(body.email) > 255:
        raise HTTPException(status_code=400, detail="Email must be 255 characters or less")
    if len(body.password) > 255:
        raise HTTPException(status_code=400, detail="Password must be 255 characters or less")
    if body.phone and len(body.phone) > 50:
        raise HTTPException(status_code=400, detail="Phone must be 50 characters or less")

    if not is_valid_email(body.email.strip()):
        raise HTTPException(status_code=400, detail="Invalid email format")

    try:
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": body.email.lower().strip()}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO users (id, name, email, password, phone, created_at)
            VALUES (:id, :name, :email, :password, :phone, :created_at)
        """), {
            "id":         user_id,
            "name":       body.name.strip(),
            "email":      body.email.lower().strip(),
            "password":   hash_password(body.password),
            "phone":      body.phone or "",
            "created_at": datetime.utcnow()
        })
        db.commit()

        token = create_token({"user_id": user_id, "email": body.email})
        return {
            "access_token": token,
            "token_type":   "bearer",
            "user": {
                "id":    user_id,
                "name":  body.name.strip(),
                "email": body.email.lower(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Register error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": body.email.lower()}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Email not found")

        user_dict = user._mapping

        if user_dict["password"] != hash_password(body.password):
            raise HTTPException(status_code=401, detail="Incorrect password")

        token = create_token({"user_id": str(user_dict["id"]), "email": user_dict["email"]})
        return {
            "access_token": token,
            "token_type":   "bearer",
            "user":         _build_user_response(user_dict)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_me(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        user = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": token.get("user_id")}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return _build_user_response(user._mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get me error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me")
async def update_profile(
    body: UpdateProfileRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Updates the professional profile of the logged-in user.
    Only fields that are explicitly provided in the request body will be updated.
    Fields not included in the request are left unchanged in the database.

    Frontend → DB column mapping:
        name         → name
        phone        → phone
        age          → age
        organization → organization   (hospital / billing firm / insurance company)
        department   → department     (e.g. Medical Coding, Claims & Billing)
        role         → role           (e.g. Medical Coder, Billing Specialist)
        work_email   → work_email     (professional email, separate from login email)
        fcmToken     → fcm_token      (device push notification token)
    """
    try:
        # Maps the field name in the request to the actual DB column name
        field_map = {
            "name":         "name",
            "phone":        "phone",
            "age":          "age",
            "organization": "organization",
            "department":   "department",
            "role":         "role",
            "work_email":   "work_email",
            "fcmToken":     "fcm_token",
        }

        # Pydantic v1/v2 compatibility
        body_dict = body.model_dump() if hasattr(body, "model_dump") else body.dict()

        # Only include fields the client actually sent (non-None values)
        updates = {}
        for frontend_key, db_column in field_map.items():
            value = body_dict.get(frontend_key)
            if value is not None:
                updates[db_column] = value.strip() if isinstance(value, str) else value

        # Validate lengths to avoid database 500 errors
        if updates.get("name") and len(updates["name"]) > 255:
            raise HTTPException(status_code=400, detail="Name must be 255 characters or less")
        if updates.get("phone") and len(updates["phone"]) > 50:
            raise HTTPException(status_code=400, detail="Phone must be 50 characters or less")
        if updates.get("age") and len(updates["age"]) > 10:
            raise HTTPException(status_code=400, detail="Age must be 10 characters or less")
        if updates.get("organization") and len(updates["organization"]) > 255:
            raise HTTPException(status_code=400, detail="Organization must be 255 characters or less")
        if updates.get("department") and len(updates["department"]) > 255:
            raise HTTPException(status_code=400, detail="Department must be 255 characters or less")
        if updates.get("role") and len(updates["role"]) > 255:
            raise HTTPException(status_code=400, detail="Role must be 255 characters or less")
        if updates.get("work_email") and len(updates["work_email"]) > 255:
            raise HTTPException(status_code=400, detail="Work email must be 255 characters or less")

        if not updates:
            return {"success": True, "message": "Nothing to update"}

        # Dynamically build: "name = :name, organization = :organization, ..."
        set_clause = ", ".join([f"{col} = :{col}" for col in updates.keys()])
        updates["user_id"] = token.get("user_id")

        db.execute(
            text(f"UPDATE users SET {set_clause} WHERE id = :user_id"),
            updates
        )
        db.commit()

        # Fetch and return the updated profile so the frontend stays in sync
        updated_user = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": token.get("user_id")}
        ).fetchone()

        return {
            "success": True,
            "message": "Profile updated successfully",
            "user":    _build_user_response(updated_user._mapping)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    try:
        user = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": body.email.lower()}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="No account found with this email")

        user_dict = user._mapping
        otp = generate_otp()
        store_otp(body.email.lower(), otp)

        email_sent = send_otp_email(
            to_email=body.email.lower(),
            otp=otp,
            user_name=user_dict["name"]
        )

        if email_sent:
            return {
                "message": "OTP sent to your email successfully! ✅",
                "email":   body.email,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        if not verify_otp(body.email.lower(), body.otp):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP. Please try again.")

        user = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": body.email.lower()}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.execute(
            text("UPDATE users SET password = :password WHERE email = :email"),
            {
                "password": hash_password(body.new_password),
                "email":    body.email.lower()
            }
        )
        db.commit()
        return {"message": "Password reset successfully ✅"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Reset password error: {e}")
        raise HTTPException(status_code=500, detail=str(e))