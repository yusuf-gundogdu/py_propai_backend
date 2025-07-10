from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.createdimage import CreatedImage
from app.schemas.createdimage import CreatedImageCreate, CreatedImageRead
from typing import List, Optional

router = APIRouter(prefix="/createdimages", tags=["CreatedImage"])

@router.get("/", response_model=List[CreatedImageRead])
async def list_createdimages(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), user_id: Optional[int] = None, model_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(CreatedImage)
    if user_id:
        query = query.where(CreatedImage.user_id == user_id)
    if model_id:
        query = query.where(CreatedImage.model_id == model_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{createdimage_id}", response_model=CreatedImageRead)
async def get_createdimage(createdimage_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreatedImage, createdimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreatedImage not found")
    return obj

@router.post("/", response_model=CreatedImageRead, status_code=status.HTTP_201_CREATED)
async def create_createdimage(data: CreatedImageCreate, db: AsyncSession = Depends(get_db)):
    obj = CreatedImage(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{createdimage_id}", response_model=CreatedImageRead)
async def update_createdimage(createdimage_id: int, data: CreatedImageCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreatedImage, createdimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreatedImage not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{createdimage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_createdimage(createdimage_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(CreatedImage, createdimage_id)
    if not obj:
        raise HTTPException(status_code=404, detail="CreatedImage not found")
    await db.delete(obj)
    await db.commit() 