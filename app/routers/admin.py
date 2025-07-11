from fastapi import APIRouter, Depends, HTTPException, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.generatemodellist import GenerateModelList
from app.models.generatemodelitem import GenerateModelItem
from app.models.createimagehistory import CreateImageHistory
from app.utils.auth_utils import get_current_admin, authenticate_user, create_access_token, get_current_user
import os

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

async def get_current_user_from_cookie(
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Cookie'den kullanıcı bilgisini al"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        from app.utils.auth_utils import jwt, SECRET_KEY, ALGORITHM
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin giriş sayfası"""
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Admin giriş işlemi"""
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Geçersiz kullanıcı adı veya şifre"
        })
    
    # Admin kontrolü
    if not user.is_active:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Hesabınız aktif değil"
        })
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.username})
    
    # Dashboard'a yönlendir
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        secure=True,  # HTTPS için True
        samesite="lax",
        max_age=86400  # 24 saat
    )
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Ana admin dashboard sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/api/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Admin dashboard için istatistikler"""
    
    # Kullanıcı sayısı
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar()
    
    # Aktif kullanıcı sayısı
    active_users = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_user_count = active_users.scalar()
    
    # Toplam hesap sayısı
    account_count = await db.execute(select(func.count(Account.id)))
    total_accounts = account_count.scalar()
    
    # Toplam model sayısı
    model_count = await db.execute(select(func.count(GenerateModelList.id)))
    total_models = model_count.scalar()
    
    # Toplam model öğesi sayısı
    model_item_count = await db.execute(select(func.count(GenerateModelItem.id)))
    total_model_items = model_item_count.scalar()
    
    # Toplam resim oluşturma sayısı
    image_history_count = await db.execute(select(func.count(CreateImageHistory.id)))
    total_image_histories = image_history_count.scalar()
    
    # Başarılı resim oluşturma sayısı
    successful_images = await db.execute(select(func.count(CreateImageHistory.id)).where(CreateImageHistory.status == 'success'))
    successful_image_count = successful_images.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_user_count,
        "total_accounts": total_accounts,
        "total_models": total_models,
        "total_model_items": total_model_items,
        "total_image_histories": total_image_histories,
        "successful_images": successful_image_count
    }

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Kullanıcı yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/users.html", {"request": request})

@router.get("/accounts", response_class=HTMLResponse)
async def admin_accounts(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Hesap yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/accounts.html", {"request": request})

@router.get("/models", response_class=HTMLResponse)
async def admin_models(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Model listesi yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/models.html", {"request": request})

@router.get("/model-items", response_class=HTMLResponse)
async def admin_model_items(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Model öğeleri yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/model_items.html", {"request": request})

@router.get("/model-images", response_class=HTMLResponse)
async def admin_model_images(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Model resimleri yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/model_images.html", {"request": request})

@router.get("/images", response_class=HTMLResponse)
async def admin_images(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Resim oluşturma sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/images.html", {"request": request})

@router.get("/image-history", response_class=HTMLResponse)
async def admin_image_history(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Resim oluşturma geçmişi yönetimi sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/image_history.html", {"request": request})

@router.get("/api-docs", response_class=HTMLResponse)
async def admin_api_docs(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """API dokümantasyon sayfası"""
    # Admin kontrolü
    if current_user.id != 1:  # Varsayılan admin ID'si
        return RedirectResponse(url="/admin/", status_code=302)
    return templates.TemplateResponse("admin/api_docs.html", {"request": request})

@router.get("/logout")
async def admin_logout():
    """Admin çıkış işlemi"""
    response = RedirectResponse(url="/admin/", status_code=302)
    response.delete_cookie(key="access_token")
    return response 