"""
Authentication and security utilities.
"""
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from ..config import JWT_SECRET_KEY

# สำหรับ Hash Password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ตั้งค่า Secret Key สำหรับ JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Generate a hash for a plain password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict):
    """
    Create a new JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
