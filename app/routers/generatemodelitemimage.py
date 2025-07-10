from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.schemas.generatemodelitemimage import GenerateModelItemImageCreate, GenerateModelItemImageRead
from typing import List, Optional
from app.models.generatemodelitem import GenerateModelItem
from pydantic import BaseModel

router = APIRouter(prefix="/generatemodelitemimages", tags=["GenerateModelItemImage"])

@router.get("/", response_model=List[GenerateModelItemImageRead])
async def list_images(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000), db: AsyncSession = Depends(get_db)):
    query = select(GenerateModelItemImage)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{image_id}", response_model=GenerateModelItemImageRead)
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItemImage not found")
    return obj

@router.post("/", response_model=GenerateModelItemImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image_no_model(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    save_dir = "generate_image"
    os.makedirs(save_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    unique_id = str(uuid4())
    file_name = f"{unique_id}{ext}"
    file_path = os.path.join(save_dir, file_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    obj = GenerateModelItemImage(
        fileName=file_name,
        filePath=file_path,
        fileSize=len(content)
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return obj

class AssignImageModel(BaseModel):
    model_id: int

@router.put("/{image_id}/assign_model", response_model=GenerateModelItemImageRead)
async def assign_image_to_model(
    image_id: int,
    data: AssignImageModel,
    db: AsyncSession = Depends(get_db)
):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Image not found")
    obj.model_id = data.model_id
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/{image_id}", response_model=GenerateModelItemImageRead)
async def update_image(image_id: int, data: GenerateModelItemImageCreate, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItemImage not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItemImage not found")
    await db.delete(obj)
    await db.commit() 