from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead
from typing import List, Optional

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("/", response_model=List[AccountRead])
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    udid: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Account)
    if udid:
        query = query.where(Account.udid == udid)
    if platform:
        query = query.where(Account.platform == platform)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{account_id}", response_model=AccountRead)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

from app.models.account import PlatformEnum

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
        credit=100
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(get_db)):
    db_account = Account(**account.model_dump())
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account

@router.put("/{account_id}", response_model=AccountRead)
async def update_account(account_id: int, account: AccountCreate, db: AsyncSession = Depends(get_db)):
    db_account = await db.get(Account, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    for key, value in account.model_dump(exclude_unset=True).items():
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