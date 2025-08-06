from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import json
import os

from app.models.createimagehistory import CreateImageHistory
from app.database import async_session
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

router = APIRouter()

@router.post("/upload-generated-image")
async def upload_generated_image(
    json_str: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        data = json.loads(json_str)
        action = data.get("action")
        generate_id = data.get("generate_id")
        udid = data.get("udid")
        generate_duration_ms = data.get("generate_duration_ms")
        if not (action and generate_id and udid):
            raise HTTPException(status_code=400, detail="Eksik json alanı")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON parse hatası: {e}")

    ext = os.path.splitext(file.filename)[1] or ".png"
    save_dir = os.path.join(os.getcwd(), "generate_image")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{generate_id}{ext}")
    with open(save_path, "wb") as f:
        f.write(await file.read())

    server_url = os.getenv("SERVER_URL", "https://propai.store")
    image_url = f"{server_url}/images/generate_image/{generate_id}{ext}"

    # --- DB'de ilgili history kaydını güncelle ---
    async with async_session() as session:
        result = await session.execute(
            select(CreateImageHistory).where(CreateImageHistory.generate_id == generate_id)
        )
        history = result.scalar_one_or_none()
        if history:
            history.status = 'success'
            # Sadece dosya adını kaydet, tam path değil:
            history.generated_image_path = f"images/generate_image/{generate_id}{ext}"
            history.generated_file_name = f"{generate_id}{ext}"
            history.generated_file_size = os.path.getsize(save_path)
            history.completed_at = datetime.utcnow()

            # Öncelik: generate_duration_ms varsa onu kullan
            if generate_duration_ms is not None:
                try:
                    ms = int(generate_duration_ms)
                    history.processing_time_seconds = int((ms + 999) // 1000)  # ms'yi yukarı yuvarla
                except Exception:
                    history.processing_time_seconds = None
            elif history.started_at and history.completed_at:
                delta = history.completed_at - history.started_at
                history.processing_time_seconds = int(delta.total_seconds())
            else:
                history.processing_time_seconds = None

            await session.commit()

    return {"status": "ok", "image_url": image_url, "generate_id": generate_id, "udid": udid}
