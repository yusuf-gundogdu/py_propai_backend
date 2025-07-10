from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.generatemodelitem import GenerateModelItemCreate, GenerateModelItemRead
from typing import List, Optional

router = APIRouter(prefix="/generatemodelitems", tags=["GenerateModelItem"])

@router.get("/", response_model=List[GenerateModelItemRead])
async def list_items(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), list_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelItem)
    if list_id:
        query = query.where(GenerateModelItem.list_id == list_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{item_id}", response_model=GenerateModelItemRead)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItem not found")
    return obj

@router.post("/", response_model=GenerateModelItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: GenerateModelItemCreate, db: AsyncSession = Depends(get_db)):
    obj = GenerateModelItem(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{item_id}", response_model=GenerateModelItemRead)
async def update_item(item_id: int, data: GenerateModelItemCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItem not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItem not found")
    await db.delete(obj)
    await db.commit() 