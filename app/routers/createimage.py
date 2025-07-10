from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.createimage import CreateImage
from app.schemas.createimage import CreateImageCreate, CreateImageRead
from typing import List, Optional

router = APIRouter(prefix="/createimages", tags=["CreateImage"])

@router.get("/", response_model=List[CreateImageRead])
async def list_createimages(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), user_id: Optional[int] = None, model_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(CreateImage)
    if user_id:
        query = query.where(CreateImage.user_id == user_id)
    if model_id:
        query = query.where(CreateImage.model_id == model_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{createimage_id}", response_model=CreateImageRead)
async def get_createimage(createimage_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreateImage, createimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreateImage not found")
    return obj

@router.post("/", response_model=CreateImageRead, status_code=status.HTTP_201_CREATED)
async def create_createimage(data: CreateImageCreate, db: AsyncSession = Depends(get_db)):
    obj = CreateImage(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{createimage_id}", response_model=CreateImageRead)
async def update_createimage(createimage_id: int, data: CreateImageCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreateImage, createimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreateImage not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{createimage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_createimage(createimage_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreateImage, createimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreateImage not found")
    await db.delete(obj)
    await db.commit() 