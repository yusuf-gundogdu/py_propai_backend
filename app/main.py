from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy import text
from app.routers.auth import router as auth_router
from app.docs_auth import router as docs_auth_router
from app.routers.admin import router as admin_router
from app.database import engine, get_db
from app.models.base import Base
from app import models
from app.routers.user import router as user_router
from app.routers.account import router as account_router
from app.routers.generatemodellist import router as generatemodellist_router
from app.routers.generatemodelitem import router as generatemodelitem_router
from app.routers.generatemodelitemimage import router as generatemodelitemimage_router
from app.routers.createimagehistory import router as createimagehistory_router
from app.routers.generate import router as generate_router
from app.routers.userupload import router as userupload_router
from app.routers.aigenerated import router as aigenerated_router
from app.models.account import Account
from app.models.user import User
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.models.createimagehistory import CreateImageHistory
import os


app = FastAPI(
    title="PropAI",
    version="v0.0.1",
    docs_url=None,  # Varsayılan docs route'unu devre dışı bırak
    redoc_url=None  # Varsayılan redoc route'unu da devre dışı bırak
)

templates = Jinja2Templates(directory="app/templates")
# İstek loglama middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"\n--- {request.method} {request.url} ---")
        print("Headers:")
        for k, v in request.headers.items():
            print(f"  {k}: {v}")
        body = await request.body()
        if body:
            try:
                print(f"Body:\n{body.decode()}")
            except Exception:
                print("Body: <binary content>")
        else:
            print("Body: <empty>")
        response = await call_next(request)
        print("--- Request ended ---\n")
        return response

app.add_middleware(LoggingMiddleware)

# Router'ları ekle
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(docs_auth_router)
app.include_router(admin_router)
app.include_router(user_router, prefix="/api")
app.include_router(account_router, prefix="/api")
app.include_router(generatemodellist_router, prefix="/api")
app.include_router(generatemodelitem_router, prefix="/api")
app.include_router(generatemodelitemimage_router, prefix="/api")
app.include_router(createimagehistory_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(userupload_router, prefix="/api")
app.include_router(aigenerated_router, prefix="/api")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Ana sayfa"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/docs", response_class=HTMLResponse)
async def custom_docs(request: Request):
    """Özelleştirilmiş Swagger UI sayfası"""
    return templates.TemplateResponse("swagger_custom.html", {"request": request})

@app.get("/redoc", response_class=HTMLResponse)
async def custom_redoc(request: Request):
    """Özelleştirilmiş ReDoc sayfası"""
    return templates.TemplateResponse("redoc_custom.html", {"request": request})

@app.on_event("startup")
async def startup():
    print("SQLAlchemy'nin gördüğü tablolar:", Base.metadata.tables.keys())
    
    # Gerekli klasörleri oluştur
    import os
    folders = ["ai_generated", "user_uploads", "generate_image"]
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Klasör oluşturuldu/kontrol edildi: {folder}")
        except Exception as e:
            print(f"❌ Klasör oluşturma hatası {folder}: {e}")
    
    # Veritabanı işlemleri
    async with engine.begin() as conn:
        # Önce eski account_id alanını sil (bir kerelik)
        try:
            await conn.execute(text("ALTER TABLE create_image_history DROP COLUMN IF EXISTS account_id"))
            print("Removed obsolete account_id column from create_image_history")
        except Exception as e:
            print(f"Error removing account_id column: {e}")
        
        # Sonra tabloları oluştur
        await conn.run_sync(Base.metadata.create_all)
    # Admin kullanıcıyı oluştur
    from sqlalchemy.future import select
    from app.utils.auth_utils import get_password_hash
    import os
    from app.database import async_session
    USERNAME = os.getenv("BASIC_AUTH_USERNAME")
    PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")
    if USERNAME and PASSWORD:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == USERNAME))
            admin = result.scalar_one_or_none()
            if not admin:
                admin = User(
                    username=USERNAME,
                    hashed_password=get_password_hash(PASSWORD),
                    is_active=True
                )
                session.add(admin)
                await session.commit()

@app.get("/images/user_uploads/{filename}")
async def serve_user_image(filename: str):
    """Kullanıcı yüklemelerini sun"""
    file_path = os.path.join("user_uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.get("/images/generate_image/{filename}")
async def serve_generated_image(filename: str):
    """Generate edilmiş resimleri sun"""
    file_path = os.path.join("generate_image", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.get("/images/ai_generated/{filename}")
async def serve_ai_generated_image(filename: str):
    """AI tarafından oluşturulan resimleri sun"""
    file_path = os.path.join("ai_generated", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)