from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/list-generated-images")
async def list_generated_images():
    folder = os.path.join(os.getcwd(), "generate_image")
    if not os.path.exists(folder):
        return {"images": []}
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    images = []
    for f in files:
        images.append({
            "filename": f,
            "url": f"/generate_image/{f}"
        })
    return {"images": images}
