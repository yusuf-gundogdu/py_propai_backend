from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema
from app.utils.auth_utils import get_password_hash, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])

# Kullanıcı oluşturma (Sadece admin)
@router.post("/", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Kullanıcı var mı kontrolü
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already registered"
        )
    
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Tüm kullanıcıları listeleme (Sadece admin)
@router.get("/", response_model=list[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

# Kullanıcı silme (Admin hariç)
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    if user_id == 1:  # Admin ID'si
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete default admin user"
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"status": "success"}

@router.post("/register")
async def register_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Kullanıcı var mı kontrolü
    existing_user = await db.execute(select(User).where(User.username == user.username))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="username already registered")
    
    # Yeni kullanıcı oluştur
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User created successfully"}