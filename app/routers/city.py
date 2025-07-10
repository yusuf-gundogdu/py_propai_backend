from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete
from app.database import get_db
from app.models.city import City
from app.schemas.city import CityCreate, CityResponse, CityUpdate
from typing import List, Optional
from datetime import datetime

router = APIRouter(
    prefix="/api/city",
    tags=["City"]
)

@router.get("/", response_model=List[CityResponse])
async def get_city(
    city_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    query = select(City)
    
    conditions = []
    
    if city_id:
        conditions.append(City.id == city_id)
    if name:
        conditions.append(City.name == name)
    if name_contains:
        conditions.append(City.name.ilike(f"%{name_contains}%"))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query.order_by(City.id).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(city: CityCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(City).where(City.name == city.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="City exists")
    
    db_city = City(**city.model_dump())
    db.add(db_city)
    await db.commit()
    await db.refresh(db_city)
    return db_city

@router.put("/{city_id}", response_model=CityResponse)
async def update_city(
    city_id: int,
    city_data: CityUpdate,
    db: AsyncSession = Depends(get_db)
):
    city = await db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    if city_data.name and city_data.name != city.name:
        existing = await db.execute(
            select(City)
            .where(City.name == city_data.name)
            .where(City.id != city_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="City name exists")
    
    for key, value in city_data.model_dump(exclude_unset=True).items():
        setattr(city, key, value)
    
    await db.commit()
    await db.refresh(city)
    return city

@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        delete(City)
        .where(City.id == city_id)
        .returning(City)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="City not found")
    await db.commit()