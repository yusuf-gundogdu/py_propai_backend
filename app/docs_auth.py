from fastapi import Depends, APIRouter
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
import secrets
import os
from dotenv import load_dotenv

load_dotenv()


USERNAME = os.getenv("BASIC_AUTH_USERNAME")
PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

security = HTTPBasic()
router = APIRouter()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if not USERNAME or not PASSWORD:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama yapılandırılmamış. Lütfen .env dosyanı kontrol et.",
            headers={"WWW-Authenticate": "Basic"},
        )
    correct_username = secrets.compare_digest(str(credentials.username), str(USERNAME))
    correct_password = secrets.compare_digest(str(credentials.password), str(PASSWORD))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kimlik bilgileri",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


