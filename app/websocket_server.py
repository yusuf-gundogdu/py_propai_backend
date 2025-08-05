import json
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import hashlib
import secrets

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.authenticated_clients: Dict[str, dict] = {}
        
        # WebSocket için kullanıcı adı ve şifre (environment'tan alınabilir)
        self.ws_username = "generate_machine"
        self.ws_password = "SecurePassword123!"  # Gerçek uygulamada environment'tan al
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """WebSocket bağlantısını kabul et"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"🔌 WebSocket bağlantısı kabul edildi: {client_id}")
        
    def disconnect(self, client_id: str):
        """WebSocket bağlantısını kapat"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.authenticated_clients:
            del self.authenticated_clients[client_id]
        print(f"❌ WebSocket bağlantısı kesildi: {client_id}")
    
    def authenticate(self, client_id: str, username: str, password: str) -> bool:
        """Kullanıcı adı ve şifre ile authentication"""
        if username == self.ws_username and password == self.ws_password:
            self.authenticated_clients[client_id] = {
                "username": username,
                "authenticated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
            print(f"✅ WebSocket authentication başarılı: {client_id} ({username})")
            return True
        else:
            print(f"❌ WebSocket authentication başarısız: {client_id} ({username})")
            return False
    
    def is_authenticated(self, client_id: str) -> bool:
        """Client'ın authenticate olup olmadığını kontrol et"""
        return client_id in self.authenticated_clients
    
    async def send_message(self, client_id: str, message: dict):
        """Belirli bir client'a mesaj gönder"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(json.dumps(message))
                
                # Son aktivite zamanını güncelle
                if client_id in self.authenticated_clients:
                    self.authenticated_clients[client_id]["last_activity"] = datetime.utcnow()
                    
            except Exception as e:
                print(f"❌ Mesaj gönderme hatası {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: dict):
        """Tüm authenticated client'lara mesaj gönder"""
        for client_id in list(self.authenticated_clients.keys()):
            await self.send_message(client_id, message)
    
    async def send_generate_request(self, client_id: str, generate_request: dict):
        """Generate makinasına resim generate isteği gönder - yeni data formatında"""
        message = {
            "type": "generate_request",
            "data": generate_request,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_message(client_id, message)
    
    def get_authenticated_clients(self) -> list:
        """Authenticated client'ların listesini döndür"""
        return list(self.authenticated_clients.keys())

# Global WebSocket manager instance
ws_manager = WebSocketManager()

async def handle_websocket_message(client_id: str, message_data: dict):
    """WebSocket'ten gelen mesajları işle"""
    try:
        message_type = message_data.get("type")
        
        if message_type == "auth":
            # Authentication mesajı
            username = message_data.get("username")
            password = message_data.get("password")
            
            if ws_manager.authenticate(client_id, username, password):
                await ws_manager.send_message(client_id, {
                    "type": "auth_response",
                    "status": "authenticated",
                    "message": "Authentication successful",
                    "client_id": client_id
                })
            else:
                await ws_manager.send_message(client_id, {
                    "type": "auth_response", 
                    "status": "failed",
                    "message": "Authentication failed"
                })
                
        elif message_type == "ping":
            # Ping mesajı - pong ile cevap ver
            await ws_manager.send_message(client_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        elif message_type == "generate_result":
            # Generate işlemi sonucu - base64 resim ile
            if ws_manager.is_authenticated(client_id):
                # Generate sonucunu database'e kaydet (base64 resmi dosyaya çevir)
                await process_generate_result(message_data)
                
                # Generate makinasına onay gönder
                history_id = message_data.get("history_id")
                response = {
                    "type": "generate_result_response",
                    "history_id": history_id,
                    "status": "received",
                    "message": "Resim başarıyla kaydedildi ve kullanıcı galerisine eklendi"
                }
                
                # Başarılı ise dosya bilgilerini de gönder
                if message_data.get("status") == "success":
                    generated_filename = message_data.get("generated_file_name")
                    if generated_filename:
                        response["saved_path"] = f"ai_generated/{generated_filename}"
                        response["public_url"] = f"https://propai.store/api/aigenerated/{generated_filename}"
                
                await ws_manager.send_message(client_id, response)
            else:
                await ws_manager.send_message(client_id, {
                    "type": "error",
                    "message": "Not authenticated"
                })
                
        elif message_type == "status":
            # Status mesajı
            if ws_manager.is_authenticated(client_id):
                await ws_manager.send_message(client_id, {
                    "type": "status_response",
                    "authenticated": True,
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                await ws_manager.send_message(client_id, {
                    "type": "status_response",
                    "authenticated": False,
                    "message": "Not authenticated"
                })
        else:
            print(f"⚠️  Bilinmeyen mesaj tipi: {message_type}")
            
    except Exception as e:
        print(f"❌ WebSocket mesaj işleme hatası: {e}")
        await ws_manager.send_message(client_id, {
            "type": "error",
            "message": f"Message processing error: {str(e)}"
        })

async def process_generate_result(result_data: dict):
    """Generate sonucunu database'e kaydet - base64 resmi dosyaya çevir"""
    try:
        from app.database import async_session
        from sqlalchemy.future import select
        from app.models.createimagehistory import CreateImageHistory
        import base64
        import os
        from uuid import uuid4
        
        history_id = result_data.get("history_id")
        status = result_data.get("status")  # "success" veya "failed"
        
        if not history_id or not status:
            print(f"❌ Eksik veri: history_id={history_id}, status={status}")
            return
        
        async with async_session() as db:
            # History kaydını bul
            query = select(CreateImageHistory).where(CreateImageHistory.id == history_id)
            result = await db.execute(query)
            history = result.scalar_one_or_none()
            
            if not history:
                print(f"❌ History {history_id} bulunamadı")
                return
            
            # History'yi güncelle
            history.status = status
            history.completed_at = datetime.utcnow()
            history.processing_time_seconds = result_data.get("processing_time_seconds", 0)
            
            if status == "success":
                # Base64 resmi kaydet
                base64_image = result_data.get("generated_image_base64")
                if base64_image:
                    try:
                        # Base64'ü decode et
                        image_data = base64.b64decode(base64_image)
                        
                        # Dosya adı oluştur (mevcut sisteme uygun)
                        generated_filename = f"ai_{uuid4()}.png"
                        generated_path = f"/api/aigenerated/{generated_filename}"
                        
                        # AI generated klasörüne kaydet (mevcut yapıya uygun)
                        ai_generated_dir = "ai_generated"
                        os.makedirs(ai_generated_dir, exist_ok=True)
                        file_path = os.path.join(ai_generated_dir, generated_filename)
                        
                        # Resmi dosyaya yaz
                        with open(file_path, "wb") as f:
                            f.write(image_data)
                        
                        file_size = len(image_data)
                        
                        # History'yi güncelle (mevcut sisteme uygun)
                        history.generated_image_path = generated_path
                        history.generated_file_name = generated_filename
                        history.generated_file_size = file_size
                        
                        print(f"✅ Base64 resmi dosyaya kaydedildi: {file_path} (Boyut: {file_size} bytes)")
                        
                    except Exception as e:
                        print(f"❌ Base64 resmi kaydetme hatası: {e}")
                        # Hata durumunda başarısız olarak işaretle
                        history.status = "failed"
                        history.error_message = f"Resim kaydetme hatası: {str(e)}"
                        
                        # Krediyi geri ver
                        from app.models.account import Account
                        account_query = select(Account).where(Account.udid == history.udid)
                        account_result = await db.execute(account_query)
                        account = account_result.scalar_one_or_none()
                        
                        if account:
                            account.credit += history.credit
                            print(f"💰 Hata nedeniyle kredi geri verildi: {history.credit}")
                        
                        await db.commit()
                        return
                else:
                    # Base64 resmi yok, eski formatı dene
                    history.generated_image_path = result_data.get("generated_image_path")
                    history.generated_file_name = result_data.get("generated_file_name")
                    history.generated_file_size = result_data.get("generated_file_size")
                
                # Metadata varsa JSON olarak kaydet
                metadata = result_data.get("metadata")
                if metadata:
                    import json
                    history.metadata = json.dumps(metadata)
                
                print(f"✅ Generate başarılı: {history_id}")
                
            else:
                # Başarısız durum
                error_message = result_data.get("error_message", "Unknown error")
                error_code = result_data.get("error_code", "UNKNOWN")
                history.error_message = f"{error_code}: {error_message}"
                
                print(f"❌ Generate başarısız: {history_id} - {error_message}")
                
                # Krediyi geri ver
                from app.models.account import Account
                account_query = select(Account).where(Account.udid == history.udid)
                account_result = await db.execute(account_query)
                account = account_result.scalar_one_or_none()
                
                if account:
                    account.credit += history.credit
                    print(f"💰 Kredi geri verildi: {history.credit}")
            
            await db.commit()
            print(f"💾 Database güncellendi: {history_id}")
            
    except Exception as e:
        print(f"❌ Generate sonucu işleme hatası: {e}")
