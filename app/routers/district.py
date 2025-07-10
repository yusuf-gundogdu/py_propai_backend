from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete
from app.database import get_db
from app.models.district import District
from app.models.city import City
from app.schemas.district import DistrictCreate, DistrictResponse, DistrictUpdate
from typing import List, Optional
from datetime import datetime

router = APIRouter(
    prefix="/api/districts",
    tags=["Districts"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[DistrictResponse])
async def get_districts(
    district_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    city_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    query = select(District)
    
    conditions = []
    
    if district_id:
        conditions.append(District.id == district_id)
    if name:
        conditions.append(District.name == name)
    if name_contains:
        conditions.append(District.name.ilike(f"%{name_contains}%"))
    if city_id:
        conditions.append(District.city_id == city_id)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query.order_by(District.id).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=DistrictResponse, status_code=status.HTTP_201_CREATED)
async def create_district(district: DistrictCreate, db: AsyncSession = Depends(get_db)):
    # Şehir var mı kontrolü
    city = await db.get(City, district.city_id)
    if not city:
        raise HTTPException(status_code=400, detail="City not found")
    
    # Aynı isimde ilçe var mı kontrolü
    existing = await db.execute(
        select(District)
        .where(District.name == district.name)
        .where(District.city_id == district.city_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="District already exists in this city")
    
    db_district = District(**district.model_dump())
    db.add(db_district)
    await db.commit()
    await db.refresh(db_district)
    return db_district

@router.put("/{district_id}", response_model=DistrictResponse)
async def update_district(
    district_id: int,
    district_data: DistrictUpdate,
    db: AsyncSession = Depends(get_db)
):
    district = await db.get(District, district_id)
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    if district_data.city_id:
        city = await db.get(City, district_data.city_id)
        if not city:
            raise HTTPException(status_code=400, detail="City not found")
    
    if district_data.name and district_data.name != district.name:
        existing = await db.execute(
            select(District)
            .where(District.name == district_data.name)
            .where(District.city_id == district_data.city_id or district.city_id)
            .where(District.id != district_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="District name exists in this city")
    
    for key, value in district_data.model_dump(exclude_unset=True).items():
        setattr(district, key, value)
    
    await db.commit()
    await db.refresh(district)
    return district

@router.delete("/{district_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_district(
    district_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        delete(District)
        .where(District.id == district_id)
        .returning(District)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="District not found")
    await db.commit()