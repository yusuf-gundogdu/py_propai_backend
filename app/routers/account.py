from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import FileResponse
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.account import Account, PlatformEnum
from app.schemas.account import AccountRead, AccountUpdate
from pydantic import BaseModel
from typing import List, Optional
import time

router = APIRouter(prefix="/account", tags=["Account"])

class AccountCreate(BaseModel):
    udid: str
    platform: PlatformEnum

@router.get("/", response_model=List[AccountRead])
async def list_accounts(
    udid: str = None,
    platform: PlatformEnum = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Account)
    if udid:
        query = query.where(Account.udid == udid)
    if platform:
        query = query.where(Account.platform == platform)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=AccountRead)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(get_db)):
    # Hesap var mı kontrolü
    result = await db.execute(select(Account).where(Account.udid == account.udid, Account.platform == account.platform))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists"
        )
    
    new_account = Account(
        udid=account.udid,
        platform=account.platform,
        level=0,
        credit=100,
        timestamp=int(time.time())
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account

@router.get("/{platform}/{udid}", response_model=AccountRead)
async def get_or_create_account(platform: PlatformEnum, udid: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.udid == udid, Account.platform == platform))
    account = result.scalar_one_or_none()
    if account:
        return account
    # Yoksa oluştur
    new_account = Account(
        udid=udid,
        platform=platform,
        level=0,
        credit=100,
        timestamp=int(time.time())
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account

@router.patch("/{account_id}", response_model=AccountRead)
async def patch_account(account_id: int, account: AccountUpdate = Body(...), db: AsyncSession = Depends(get_db)):
    db_account = await db.get(Account, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    update_data = account.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)
    await db.commit()
    await db.refresh(db_account)
    return db_account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    db_account = await db.get(Account, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(db_account)
    await db.commit()

@router.get("/image/{image_path:path}")
async def get_image(image_path: str):
    # Güvenlik için path traversal saldırılarını engelle
    if ".." in image_path or image_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid image path")

    # Resim dosyasının tam yolunu oluştur
    # Örnek: /uploads/images/ klasöründen servis et
    image_dir = "/uploads/images"  # Bu yolu ihtiyacına göre değiştir
    full_path = os.path.join(image_dir, image_path)

    # Dosyanın var olup olmadığını kontrol et
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Dosyayı döndür
    return FileResponse(full_path) 