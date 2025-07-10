from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete
from app.database import get_db
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from typing import List, Optional
from datetime import datetime

router = APIRouter(
    prefix="/api/roles",
    tags=["Roles"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    role_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    name_contains: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    query = select(Role)
    
    conditions = []
    
    if role_id:
        conditions.append(Role.id == role_id)
    if name:
        conditions.append(Role.name == name)
    if name_contains:
        conditions.append(Role.name.ilike(f"%{name_contains}%"))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query.order_by(Role.id).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Role)
        .where(Role.name == role.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    
    db_role = Role(**role.model_dump())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role_data.name and role_data.name != role.name:
        existing = await db.execute(
            select(Role)
            .where(Role.name == role_data.name)
            .where(Role.id != role_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Role name already exists")
    
    for key, value in role_data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    
    await db.commit()
    await db.refresh(role)
    return role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        delete(Role)
        .where(Role.id == role_id)
        .returning(Role)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Role not found")
    await db.commit()