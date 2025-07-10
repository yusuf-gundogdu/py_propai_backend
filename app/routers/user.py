from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, User as UserSchema
from app.utils.auth_utils import get_password_hash, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])

# Default admin kullanıcı oluştur
async def create_default_user():
    async with engine.begin() as conn:
        async with AsyncSession(conn) as db:
            try:
                # Önce administrator rolünü oluştur (eğer yoksa)
                admin_role = await db.execute(select(Role).where(Role.name == "administrator"))
                admin_role = admin_role.scalar_one_or_none()
                
                if not admin_role:
                    admin_role = Role(name="administrator")
                    db.add(admin_role)
                    await db.commit()
                    await db.refresh(admin_role)
                    print(f"✅ Administrator rolü oluşturuldu (ID: {admin_role.id})")
                else:
                    print(f"✅ Administrator rolü zaten mevcut (ID: {admin_role.id})")
                
                # Admin kullanıcısını kontrol et
                result = await db.execute(select(User).where(User.username == "admin"))
                existing_admin = result.scalar_one_or_none()
                
                if not existing_admin:
                    admin = User(
                        username="admin",
                        hashed_password=get_password_hash("190943"),
                        is_active=True,
                        role_id=admin_role.id  # Administrator rolünü ata
                    )
                    db.add(admin)
                    await db.commit()
                    await db.refresh(admin)
                    print(f"✅ Admin kullanıcısı oluşturuldu (ID: {admin.id}, Role ID: {admin.role_id})")
                else:
                    # Eğer admin varsa ama role_id yoksa, role_id'yi güncelle
                    if existing_admin.role_id is None:
                        existing_admin.role_id = admin_role.id
                        await db.commit()
                        await db.refresh(existing_admin)
                        print(f"✅ Mevcut admin kullanıcısına role atandı (ID: {existing_admin.id}, Role ID: {existing_admin.role_id})")
                    else:
                        print(f"✅ Admin kullanıcısı zaten mevcut (ID: {existing_admin.id}, Role ID: {existing_admin.role_id})")
            except Exception as e:
                await db.rollback()
                print(f"❌ Hata: {e}")
                raise e

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