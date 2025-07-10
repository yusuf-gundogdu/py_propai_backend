from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.generatemodellist import GenerateModelListCreate, GenerateModelListRead
from typing import List, Optional

router = APIRouter(prefix="/generatemodellists", tags=["GenerateModelList"])

@router.get("/", response_model=List[GenerateModelListRead])
async def list_lists(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelList)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{list_id}", response_model=GenerateModelListRead)
async def get_list(list_id: int, db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelList).where(GenerateModelList.id == list_id)
    result = await db.execute(query)
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelList not found")
    return obj

@router.post("/", response_model=GenerateModelListRead, status_code=status.HTTP_201_CREATED)
async def create_list(data: GenerateModelListCreate, db: AsyncSession = Depends(get_db)):
    # item_ids'leri kontrol et ve gerekirse otomatik oluştur
    if data.item_ids:
        for item_id in data.item_ids:
            # Önce mevcut item'ı ara
            item = await db.get(GenerateModelItem, item_id)
            if not item:
                # Eğer yoksa otomatik oluştur
                item = GenerateModelItem(
                    id=item_id,
                    name=f"Auto Generated Item {item_id}",
                    credit=10,
                    level=1,
                    image_id=None  # image_id'yi None olarak ayarla
                )
                db.add(item)
    
    obj = GenerateModelList(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{list_id}", response_model=GenerateModelListRead)
async def update_list(list_id: int, data: GenerateModelListCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelList, list_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelList not found")
    
    # item_ids'leri kontrol et ve gerekirse otomatik oluştur
    if data.item_ids:
        for item_id in data.item_ids:
            # Önce mevcut item'ı ara
            item = await db.get(GenerateModelItem, item_id)
            if not item:
                # Eğer yoksa otomatik oluştur
                item = GenerateModelItem(
                    id=item_id,
                    name=f"Auto Generated Item {item_id}",
                    credit=10,
                    level=1,
                    image_id=None  # image_id'yi None olarak ayarla
                )
                db.add(item)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelList, list_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelList not found")
    await db.delete(obj)
    await db.commit() 