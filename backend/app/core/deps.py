import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rainbow-bridge-secret-change-in-prod")
_ALGORITHM = "HS256"

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        payload = jwt.decode(
            credentials.credentials, _SECRET_KEY, algorithms=[_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="인증 정보가 유효하지 않습니다."
            )
        return {"user_id": int(user_id), "email": payload.get("email", "")}
    except JWTError:
        raise HTTPException(status_code=401, detail="인증 정보가 유효하지 않습니다.")
