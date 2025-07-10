from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
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