from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.generatemodellist import GenerateModelListCreate, GenerateModelListRead, GenerateModelListUpdate
from typing import List, Optional

router = APIRouter(prefix="/generatemodellists", tags=["GenerateModelList"])

@router.get("/", response_model=List[GenerateModelListRead])
async def list_lists(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelList)
    result = await db.execute(query.offset(skip).limit(limit))
    lists = result.scalars().all()
    
    # Her liste için item'ları yükle
    for list_obj in lists:
        if list_obj.item_ids:
            # item_ids'den GenerateModelItem nesnelerini yükle
            items_query = select(GenerateModelItem).options(joinedload(GenerateModelItem.image)).where(GenerateModelItem.id.in_(list_obj.item_ids))
            items_result = await db.execute(items_query)
            list_obj.items = items_result.scalars().all()
        else:
            list_obj.items = []
    
    return lists

@router.get("/{list_id}", response_model=GenerateModelListRead)
async def get_list(list_id: int, db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelList).where(GenerateModelList.id == list_id)
    result = await db.execute(query)
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelList not found")
    
    # Item'ları yükle
    if obj.item_ids:
        items_query = select(GenerateModelItem).options(joinedload(GenerateModelItem.image)).where(GenerateModelItem.id.in_(obj.item_ids))
        items_result = await db.execute(items_query)
        obj.items = items_result.scalars().all()
    else:
        obj.items = []
    
    return obj

@router.post("/", response_model=GenerateModelListRead, status_code=status.HTTP_201_CREATED)
async def create_list(data: GenerateModelListCreate, db: AsyncSession = Depends(get_db)):
    # Priority kontrolü ve atama
    priority = data.priority
    if priority is not None:
        # Verilen priority'de başka liste var mı kontrol et
        existing_list = await db.execute(
            select(GenerateModelList).where(GenerateModelList.priority == priority)
        )
        if existing_list.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Priority {priority} is already taken. Please choose another priority value."
            )
    else:
        # Priority verilmemişse en yüksek priority + 1 ata
        max_priority_result = await db.execute(
            select(GenerateModelList.priority).order_by(GenerateModelList.priority.desc()).limit(1)
        )
        max_priority = max_priority_result.scalar_one_or_none()
        priority = (max_priority or 0) + 1
    
    # item_ids'leri kontrol et ve gerekirse otomatik oluştur
    if data.item_ids:
        for item_id in data.item_ids:
            # Önce mevcut item'ı ara
            item = await db.get(GenerateModelItem, item_id)
            if not item:
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
                item = GenerateModelItem(
                    id=item_id,
                    name=name,  # Benzersiz isim kullan
                    credit=10,
                    level=1,
                    priority=next_priority,  # Otomatik priority ata
                    image_id=None  # image_id'yi None olarak ayarla
                )
                db.add(item)
    
    obj = GenerateModelList(
        name=data.name,
        priority=priority,
        item_ids=data.item_ids
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{list_id}", response_model=GenerateModelListRead)
async def update_list(list_id: int, data: GenerateModelListUpdate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelList, list_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelList not found")
    
    # Priority kontrolü
    if data.priority is not None:
        # Verilen priority'de başka liste var mı kontrol et (kendisi hariç)
        existing_list = await db.execute(
            select(GenerateModelList).where(
                GenerateModelList.priority == data.priority,
                GenerateModelList.id != list_id
            )
        )
        if existing_list.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Priority {data.priority} is already taken. Please choose another priority value."
            )
    
    # item_ids'leri kontrol et ve gerekirse otomatik oluştur
    if data.item_ids:
        for item_id in data.item_ids:
            # Önce mevcut item'ı ara
            item = await db.get(GenerateModelItem, item_id)
            if not item:
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
                item = GenerateModelItem(
                    id=item_id,
                    name=name,  # Benzersiz isim kullan
                    credit=10,
                    level=1,
                    priority=next_priority,  # Otomatik priority ata
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