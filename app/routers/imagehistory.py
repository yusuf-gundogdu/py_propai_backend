from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.imagehistory import ImageHistory
from app.schemas.imagehistory import ImageHistoryCreate, ImageHistoryRead
from typing import List, Optional

router = APIRouter(prefix="/imagehistories", tags=["ImageHistory"])

@router.get("/", response_model=List[ImageHistoryRead])
async def list_imagehistories(
    last_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    user_id: Optional[int] = None,
    model_id: Optional[int] = None,
    image_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(ImageHistory)
    if last_id:
        query = query.where(ImageHistory.id < last_id)
    if user_id:
        query = query.where(ImageHistory.user_id == user_id)
    if model_id:
        query = query.where(ImageHistory.model_id == model_id)
    if image_id:
        query = query.where(ImageHistory.image_id == image_id)
    query = query.order_by(ImageHistory.id.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{imagehistory_id}", response_model=ImageHistoryRead)
async def get_imagehistory(imagehistory_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(ImageHistory, imagehistory_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ImageHistory not found")
    return obj

@router.post("/", response_model=ImageHistoryRead, status_code=status.HTTP_201_CREATED)
async def create_imagehistory(data: ImageHistoryCreate, db: AsyncSession = Depends(get_db)):
    obj = ImageHistory(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{imagehistory_id}", response_model=ImageHistoryRead)
async def update_imagehistory(imagehistory_id: int, data: ImageHistoryCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(ImageHistory, imagehistory_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ImageHistory not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{imagehistory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_imagehistory(imagehistory_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(ImageHistory, imagehistory_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ImageHistory not found")
    await db.delete(obj)
    await db.commit() 