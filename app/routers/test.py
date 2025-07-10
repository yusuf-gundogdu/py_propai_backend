from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth_utils import verify_token

router = APIRouter(
    prefix="/test",
    tags=["Test"]
)

bearer_scheme = HTTPBearer()

@router.get(
    "/secure",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def secure_endpoint(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token_str = token.credentials
    try:
        payload = verify_token(token_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return {"message": f"Hello, {username}! This is a protected endpoint."}
