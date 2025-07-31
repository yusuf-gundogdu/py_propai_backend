from fastapi import Depends, APIRouter, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User

router = APIRouter()

async def get_current_user_from_cookie(
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Cookie'den kullanıcı bilgisini al - docs için"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        from app.utils.auth_utils import jwt, SECRET_KEY, ALGORITHM
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/admin/")

@router.get("/docs", response_class=HTMLResponse)
async def protected_docs():
    """Swagger UI sayfası - Middleware tarafından korunuyor"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="PropAI API")

@router.get("/redoc", response_class=HTMLResponse)  
async def protected_redoc():
    """ReDoc sayfası - Middleware tarafından korunuyor"""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url="/openapi.json", title="PropAI API")

@router.get("/openapi.json")
async def protected_openapi():
    """OpenAPI JSON - Middleware tarafından korunuyor"""
    from fastapi.openapi.utils import get_openapi
    from app.main import app
    return get_openapi(title="PropAI API", version="v0.0.1", routes=app.routes)


