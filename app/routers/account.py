from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.database import get_db
from app.models.account import Account
from app.models.city import City
from app.models.district import District
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from typing import List, Optional
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"]
)

bearer_scheme = HTTPBearer()

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    account_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    city_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None), 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme)  
):
    query = select(Account)
    conditions = []

    if account_id is not None:
        conditions.append(Account.id == account_id)
    if name is not None:
        conditions.append(Account.name == name)
    if name_contains is not None:
        conditions.append(Account.name.ilike(f"%{name_contains}%"))
    if city_id is not None:
        conditions.append(Account.city_id == city_id)
    if district_id is not None:
        conditions.append(Account.district_id == district_id)

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query.order_by(Account.id).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(get_db)):
    city = await db.get(City, account.city_id)
    if not city:
        raise HTTPException(status_code=400, detail="City not found")

    district = await db.get(District, account.district_id)
    if not district:
        raise HTTPException(status_code=400, detail="District not found")

    existing = await db.execute(select(Account).where(Account.name == account.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Account exists")

    db_account = Account(**account.model_dump())
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: AsyncSession = Depends(get_db)
):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account_data.city_id is not None:
        city = await db.get(City, account_data.city_id)
        if not city:
            raise HTTPException(status_code=400, detail="City not found")

    if account_data.district_id is not None:
        district = await db.get(District, account_data.district_id)
        if not district:
            raise HTTPException(status_code=400, detail="District not found")

    if account_data.name and account_data.name != account.name:
        existing = await db.execute(
            select(Account)
            .where(Account.name == account_data.name)
            .where(Account.id != account_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Account name exists")

    for key, value in account_data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)

    account.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(account)
    return account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme)  
):
    result = await db.execute(
        delete(Account)
        .where(Account.id == account_id)
        .returning(Account)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")
    await db.commit()
