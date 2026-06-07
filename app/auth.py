from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from app.config import settings
from app.database import parents_collection, hospitals_collection

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 7 days to match '7d' in original Node.js
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token is invalid or expired. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("id")
        user_type: str = payload.get("userType")
        if user_id is None or user_type is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from appropriate collection
    if user_type == "parent":
        user = await parents_collection.find_one({"_id": ObjectId(user_id)})
    elif user_type == "hospital":
        user = await hospitals_collection.find_one({"_id": ObjectId(user_id)})
    else:
        raise credentials_exception

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Token is invalid."
        )

    if not user.get("isActive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    # Return standard user dict mirroring req.user in Express
    return {
        "_id": str(user["_id"]),
        "id": str(user["_id"]),
        "userType": user_type,
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
    }

def authorize_roles(allowed_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["userType"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User type '{current_user['userType']}' is not authorized to access this route"
            )
        return current_user
    return role_checker
