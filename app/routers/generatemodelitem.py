from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.generatemodelitem import GenerateModelItemCreate, GenerateModelItemRead
from typing import List, Optional

router = APIRouter(prefix="/generatemodelitems", tags=["GenerateModelItem"])

@router.get("/", response_model=List[GenerateModelItemRead])
async def list_items(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelItem).options(joinedload(GenerateModelItem.image))
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{item_id}", response_model=GenerateModelItemRead)
async def get_or_create_item(item_id: int, db: AsyncSession = Depends(get_db)):
    # Önce mevcut item'ı ara
    query = select(GenerateModelItem).options(joinedload(GenerateModelItem.image)).where(GenerateModelItem.id == item_id)
    result = await db.execute(query)
    obj = result.scalar_one_or_none()
    
    if not obj:
        # En yüksek priority'yi bul
        max_priority_result = await db.execute(
            select(GenerateModelItem.priority).order_by(GenerateModelItem.priority.desc()).limit(1)
        )
        max_priority = max_priority_result.scalar_one_or_none()
        next_priority = (max_priority or 0) + 1
        
        # Benzersiz isim oluştur
        base_name = f"Auto Generated Item {item_id}"
        name = base_name
        counter = 1
        while True:
            existing_item = await db.execute(
                select(GenerateModelItem).where(GenerateModelItem.name == name)
            )
            if not existing_item.scalar_one_or_none():
                break
            name = f"{base_name} ({counter})"
            counter += 1
        
        # Eğer yoksa otomatik oluştur
        obj = GenerateModelItem(
            id=item_id,
            name=name,  # Benzersiz isim kullan
            credit=10,
            level=1,
            priority=next_priority,  # Otomatik priority ata
            image_id=None  # image_id'yi None olarak ayarla
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
    
    return obj

@router.post("/", response_model=GenerateModelItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: GenerateModelItemCreate, db: AsyncSession = Depends(get_db)):
    # image_id 0 ise None olarak ayarla
    item_data = data.model_dump()
    if item_data.get('image_id') == 0:
        item_data['image_id'] = None
    
    # Name kontrolü - aynı isimde item var mı kontrol et
    existing_item = await db.execute(
        select(GenerateModelItem).where(GenerateModelItem.name == data.name)
    )
    if existing_item.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Item with name '{data.name}' already exists. Please choose another name."
        )
    
    # Priority kontrolü ve atama
    priority = item_data.get('priority')
    if priority is not None:
        # Verilen priority'de başka item var mı kontrol et
        existing_item = await db.execute(
            select(GenerateModelItem).where(GenerateModelItem.priority == priority)
        )
        if existing_item.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Priority {priority} is already taken. Please choose another priority value."
            )
    else:
        # Priority verilmemişse en yüksek priority + 1 ata
        max_priority_result = await db.execute(
            select(GenerateModelItem.priority).order_by(GenerateModelItem.priority.desc()).limit(1)
        )
        max_priority = max_priority_result.scalar_one_or_none()
        item_data['priority'] = (max_priority or 0) + 1
    
    obj = GenerateModelItem(**item_data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    
    # image ilişkisini yüklemek için tekrar sorgu yap
    query = select(GenerateModelItem).options(joinedload(GenerateModelItem.image)).where(GenerateModelItem.id == obj.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItem not found")
    await db.delete(obj)
    await db.commit() 