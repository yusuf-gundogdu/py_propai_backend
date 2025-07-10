from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.routers.account import router as account_router
from app.routers.city import router as city_router
from app.routers.district import router as district_router
from app.routers.role import router as role_router
from app.routers.auth import router as auth_router
from app.docs_auth import router as docs_auth_router
from app.database import engine, Base, get_db
from app.routers.user import router as user_router, create_default_user


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
app.include_router(account_router)
app.include_router(city_router)
app.include_router(district_router)
app.include_router(role_router)
app.include_router(docs_auth_router)
app.include_router(user_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_default_user()