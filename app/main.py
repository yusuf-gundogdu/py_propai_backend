from fastapi import FastAPI, Depends, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
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
from app.websocket_server import ws_manager, handle_websocket_message
from app.models.account import Account
from app.models.user import User
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.models.createimagehistory import CreateImageHistory
from datetime import datetime
import os
import logging

# Performance için logging level'ını ayarla
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)


app = FastAPI(
    title="PropAI",
    version="v0.0.1",
    docs_url="/docs",  # Swagger dokümanı aktif
    redoc_url="/redoc"  # Redoc dokümanı aktif
)

templates = Jinja2Templates(directory="app/templates")

# Authentication middleware - sadece admin sayfalarını koruma altına al
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Açık kalması gereken sayfalar (admin login sayfaları)
        allowed_paths = [
            "/admin/",
            "/admin/login"
        ]
        
        # Static dosyalar, resimler ve API endpoint'leri açık kalabilir
        allowed_prefixes = [
            "/api/",          # Tüm API endpoint'leri public
            "/ws/",           # WebSocket endpoint'leri public
            "/images/",
            "/static/",
            "/favicon.ico"
        ]
        
        # Eğer açık sayfalardan biri değilse
        is_allowed = path in allowed_paths or any(path.startswith(prefix) for prefix in allowed_prefixes)
        
        if not is_allowed:
            # Ana sayfa ise admin'e yönlendir
            if path == "/":
                return RedirectResponse(url="/admin/", status_code=302)
            
            # Diğer tüm sayfalar için authentication kontrolü
            access_token = request.cookies.get("access_token")
            if not access_token:
                return RedirectResponse(url="/admin/", status_code=302)
            
            # Token'ı doğrula
            try:
                from app.utils.auth_utils import jwt, SECRET_KEY, ALGORITHM
                payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if not username:
                    return RedirectResponse(url="/admin/", status_code=302)
            except Exception:
                return RedirectResponse(url="/admin/", status_code=302)
        
        response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

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

# WebSocket endpoint
@app.websocket("/ws/generate")
async def websocket_endpoint(websocket: WebSocket):
    """
    Generate makinası için WebSocket endpoint
    Kullanıcı adı ve şifre ile authentication gerekli
    """
    import uuid
    import json
    
    client_id = str(uuid.uuid4())
    
    try:
        await ws_manager.connect(websocket, client_id)
        
        while True:
            # Mesaj al
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Mesajı işle
            await handle_websocket_message(client_id, message_data)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"❌ WebSocket hatası: {e}")
    finally:
        ws_manager.disconnect(client_id)

# WebSocket status endpoint
@app.get("/api/ws/status")
async def get_websocket_status():
    """WebSocket bağlantı durumunu kontrol et"""
    authenticated_clients = ws_manager.get_authenticated_clients()
    
    return {
        "active_connections": len(ws_manager.active_connections),
        "authenticated_clients": len(authenticated_clients),
        "client_ids": authenticated_clients,
        "timestamp": datetime.utcnow().isoformat()
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Ana sayfa - otomatik olarak admin'e yönlendirir"""
    return RedirectResponse(url="/admin/", status_code=302)

@app.on_event("startup")
async def startup():
    print("SQLAlchemy'nin gördüğü tablolar:", Base.metadata.tables.keys())
    
    # Gerekli klasörleri oluştur
    import os
    from dotenv import load_dotenv
    
    # .env dosyasını yükle
    load_dotenv()
    
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
    from app.database import async_session
    
    USERNAME = os.getenv("BASIC_AUTH_USERNAME")
    PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")
    
    print(f"Environment values - USERNAME: {USERNAME}, PASSWORD: {'***' if PASSWORD else None}")
    
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
                print(f"✅ Admin kullanıcısı oluşturuldu: {USERNAME}")
            else:
                print(f"✅ Admin kullanıcısı zaten mevcut: {USERNAME}")
    else:
        print("❌ Environment variables not found for admin user creation")
    
    # WebSocket manager'ı başlat
    print("🚀 WebSocket Manager başlatıldı!")
    print(f"📡 WebSocket endpoint: ws://localhost:8000/ws/generate")
    print(f"🔑 Auth: username=generate_machine, password=SecurePassword123!")

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