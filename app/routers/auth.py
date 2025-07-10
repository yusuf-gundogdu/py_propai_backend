from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.utils.auth_utils import verify_password, create_access_token

router = APIRouter()

@router.post("/token")
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # 1. Kullanıcıyı bul
    user = await db.execute(select(User).where(User.username == form_data.username))
    user = user.scalars().first()
    
    # 2. Şifreyi kontrol et
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yanlış kullanıcı adı/şifre",
        )
    
    # 3. Token oluştur
    return {
        "access_token": create_access_token({"sub": user.username}),
        "token_type": "bearer"
    }