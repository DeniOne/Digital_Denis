"""
Digital Den — Authentication Logic
═══════════════════════════════════════════════════════════════════════════

JWT token management and Telegram OAuth validation.
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db

# Security schemes
security = HTTPBearer()

# Constants
ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expiry_hours * 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_telegram_data(auth_data: Dict[str, Any], bot_token: str) -> bool:
    """
    Verify Telegram Login Widget data.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = auth_data.get("hash")
    if not check_hash:
        return False
    
    # Create data_check_string
    data_check_arr = []
    for key, value in auth_data.items():
        if key != "hash":
            data_check_arr.append(f"{key}={value}")
    
    data_check_string = "\n".join(sorted(data_check_arr))
    
    # Create secret key from bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    
    # Calculate HMAC
    hmac_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac_hash == check_hash


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency to get the current authenticated user.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Lazy import to avoid circular dependency
    from memory.models import User
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency to get current user with optional auth.
    In debug mode, returns a dev user if no token provided.
    """
    from core.config import settings
    
    # If credentials provided, validate normally
    if credentials:
        return await get_current_user(credentials, db)
    
    # In debug mode, allow requests without auth using dev user
    if settings.debug:
        from memory.models import User
        from sqlalchemy import select
        
        # Use the main user account for all debug requests
        result = await db.execute(
            select(User).where(User.telegram_id == 441610858)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Fallback: get any existing user
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
        if not user:
            print("DEBUG: No users found, creating one...")
            user = User(
                username="denisgovako",
                full_name="Denis Govako",
                telegram_id=441610858,
                role="owner"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"DEBUG: Created user: {user.id}")
        
        return user
    
    # In production, require auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
