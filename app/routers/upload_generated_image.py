from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import json
import os

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
    image_url = f"{server_url}/generate_image/{generate_id}{ext}"

    return {"status": "ok", "image_url": image_url, "generate_id": generate_id, "udid": udid}
