from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.routers.auth import router as auth_router
from app.docs_auth import router as docs_auth_router
from app.database import engine, get_db
from app.models.base import Base
from app import models
from app.routers.user import router as user_router
from app.routers.account import router as account_router
from app.routers.generatemodellist import router as generatemodellist_router
from app.routers.generatemodelitem import router as generatemodelitem_router
from app.routers.generatemodelitemimage import router as generatemodelitemimage_router
from app.routers.createimage import router as createimage_router
from app.routers.createdimage import router as createdimage_router
from app.routers.imagehistory import router as imagehistory_router
from app.models.account import Account
from app.models.user import User
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.models.createimage import CreateImage
from app.models.createdimage import CreatedImage
from app.models.imagehistory import ImageHistory


app = FastAPI(
    title="PropAI",
    version="v0.0.1"
)
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
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(docs_auth_router)
app.include_router(user_router)
app.include_router(account_router)
app.include_router(generatemodellist_router)
app.include_router(generatemodelitem_router)
app.include_router(generatemodelitemimage_router)
app.include_router(createimage_router)
app.include_router(createdimage_router)
app.include_router(imagehistory_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@app.on_event("startup")
async def startup():
    print("SQLAlchemy'nin gördüğü tablolar:", Base.metadata.tables.keys())
    async with engine.begin() as conn:
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