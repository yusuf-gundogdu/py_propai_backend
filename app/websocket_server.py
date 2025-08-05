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
        """Generate makinasına resim generate isteği gönder"""
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
                    "success": True,
                    "message": "Authentication successful"
                })
            else:
                await ws_manager.send_message(client_id, {
                    "type": "auth_response", 
                    "success": False,
                    "message": "Authentication failed"
                })
                
        elif message_type == "ping":
            # Ping mesajı - pong ile cevap ver
            await ws_manager.send_message(client_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        elif message_type == "generate_result":
            # Generate işlemi sonucu
            if ws_manager.is_authenticated(client_id):
                result_data = message_data.get("data", {})
                print(f"📸 Generate sonucu alındı: {result_data}")
                
                # Burada generate sonucunu database'e kaydet
                await process_generate_result(result_data)
                
                await ws_manager.send_message(client_id, {
                    "type": "result_received",
                    "success": True,
                    "message": "Generate result processed successfully"
                })
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
    """Generate sonucunu işle ve database'e kaydet"""
    try:
        # Database işlemleri için gerekli import'lar
        from app.database import async_session
        from app.models.createimagehistory import CreateImageHistory
        from sqlalchemy.future import select
        
        history_id = result_data.get("history_id")
        status = result_data.get("status")
        generated_image_path = result_data.get("generated_image_path")
        error_message = result_data.get("error_message")
        
        if not history_id:
            print("❌ History ID bulunamadı")
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
            
            if status == "success" and generated_image_path:
                history.generated_image_path = generated_image_path
                history.generated_file_name = result_data.get("generated_file_name")
                history.generated_file_size = result_data.get("generated_file_size")
                history.processing_time_seconds = result_data.get("processing_time_seconds")
                print(f"✅ Generate başarılı: {history_id}")
            else:
                history.error_message = error_message
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
