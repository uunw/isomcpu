"""
Shared dependencies for the FastAPI application.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .database import get_db
from .config import JWT_SECRET_KEY
from .models.technician import Technician

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/tech/login")

def get_current_technician(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current authenticated technician.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token ไม่ถูกต้อง",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token หมดอายุหรือผิดพลาด",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    tech = db.query(Technician).filter(Technician.email == email).first()
    if tech is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลช่าง"
        )

    return tech
