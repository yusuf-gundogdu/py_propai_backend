#!/usr/bin/env python3
"""
GENERATE MAKİNASI İÇİN WEBSOCKET CLIENT KODU
Bu kodu generate makinasına kopyalayın ve çalıştırın.

BAĞLANTI BİLGİLERİ:
- Server IP: YOUR_SERVER_IP (gerçek IP adresini yazın)
- Port: 443 (HTTPS/WSS)
- WebSocket URL: wss://YOUR_SERVER_IP:443/ws/generate
- Username: generate_machine
- Password: SecurePassword123!
- SSL: Evet (wss://)

KULLANIM:
1. YOUR_SERVER_IP yazan yeri gerçek IP ile değiştirin
2. pip install websockets
3. python3 bu_dosya.py
"""

import asyncio
import websockets
import json
import ssl
import logging
from datetime import datetime

# ===========================================
# AYARLAR - BU KISMI DEĞİŞTİRİN
# ===========================================
SERVER_IP = "propai.store"  # Backend sunucu IP/domain adresi
SERVER_PORT = 443
WEBSOCKET_URL = f"wss://{SERVER_IP}:{SERVER_PORT}/ws/generate"
USERNAME = "generate_machine"
PASSWORD = "SecurePassword123!"

# ALTERNATIF IP ADRESLERİ:
# SERVER_IP = "192.168.1.XXX"  # Yerel ağ IP'si
# SERVER_IP = "XXX.XXX.XXX.XXX"  # Dış IP adresi

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_image_with_ai(image_path, model_id):
    """
    AI ile resmi işle - BU FONKSİYONU MUTLAKA DEĞİŞTİRİN!
    """
    logger.info(f"🤖 AI işleniyor: {image_path}, Model: {model_id}")
    
    # BURAYA KENDİ AI KODUNUZU YAZIN!
    # Örnek: Stable Diffusion, Custom Model, vs.
    await asyncio.sleep(5)  # Simülasyon
    
    # AI işleminden sonra yeni resim path'i döndürün
    return f"/api/aigenerated/ai_generated_{model_id}.jpg"

async def generate_machine_client():
    """Ana WebSocket client fonksiyonu"""
    
    # SSL context (self-signed certificate için)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    while True:
        try:
            logger.info(f"🔌 Bağlanıyor: {WEBSOCKET_URL}")
            
            async with websockets.connect(WEBSOCKET_URL, ssl=ssl_context) as websocket:
                logger.info("✅ WebSocket bağlantısı başarılı!")
                
                # 1. Authentication
                auth_msg = {
                    "type": "auth",
                    "username": USERNAME,
                    "password": PASSWORD
                }
                await websocket.send(json.dumps(auth_msg))
                logger.info("📤 Authentication mesajı gönderildi")
                
                # Auth response bekle
                response = await websocket.recv()
                auth_response = json.loads(response)
                logger.info(f"📥 Auth response: {auth_response}")
                
                if auth_response.get("status") != "authenticated":
                    logger.error("❌ Authentication başarısız!")
                    continue
                
                logger.info("✅ Authentication başarılı! Mesajlar bekleniyor...")
                
                # 2. Mesajları dinle
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        
                        if msg_type == "generate_request":
                            # Generate isteği geldi
                            history_id = data.get("history_id")
                            generate_id = data.get("generate_id")
                            original_image_path = data.get("original_image_path")
                            model_id = data.get("model_id")
                            udid = data.get("udid")
                            credit = data.get("credit")
                            
                            logger.info(f"🎯 Generate isteği alındı:")
                            logger.info(f"  - History ID: {history_id}")
                            logger.info(f"  - Generate ID: {generate_id}")
                            logger.info(f"  - Image Path: {original_image_path}")
                            logger.info(f"  - Model ID: {model_id}")
                            logger.info(f"  - User ID: {udid}")
                            logger.info(f"  - Credit: {credit}")
                            
                            try:
                                # AI ile işle
                                generated_path = await process_image_with_ai(
                                    original_image_path, model_id
                                )
                                
                                # Başarılı sonuç
                                result = {
                                    "type": "generate_result",
                                    "history_id": history_id,
                                    "status": "success",
                                    "generated_image_path": generated_path,
                                    "generated_file_name": f"ai_{history_id}.jpg",
                                    "generated_file_size": 150000,
                                    "processing_time_seconds": 5
                                }
                                logger.info("✅ AI işleme başarılı")
                                
                            except Exception as e:
                                # Hata durumu
                                result = {
                                    "type": "generate_result",
                                    "history_id": history_id,
                                    "status": "failed",
                                    "error_message": str(e)
                                }
                                logger.error(f"❌ AI işleme hatası: {e}")
                            
                            await websocket.send(json.dumps(result))
                            logger.info(f"📤 Generate sonucu gönderildi: {result['status']}")
                        
                        elif msg_type == "ping":
                            # Ping'e cevap
                            pong = {
                                "type": "pong", 
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await websocket.send(json.dumps(pong))
                            logger.info("🏓 Pong gönderildi")
                            
                        else:
                            logger.info(f"� Bilinmeyen mesaj tipi: {msg_type}")
                            
                    except json.JSONDecodeError:
                        logger.error("❌ Geçersiz JSON mesajı alındı")
                    except Exception as e:
                        logger.error(f"❌ Mesaj işleme hatası: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 WebSocket bağlantısı kesildi")
        except Exception as e:
            logger.error(f"❌ Bağlantı hatası: {e}")
            
        # Yeniden bağlanmayı dene
        logger.info("🔄 30 saniye bekleyip yeniden bağlanılacak...")
        await asyncio.sleep(30)

async def test_websocket_simple():
    """Basit test fonksiyonu"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print(f"� Test bağlantısı: {WEBSOCKET_URL}")
        async with websockets.connect(WEBSOCKET_URL, ssl=ssl_context) as websocket:
            print('✅ WebSocket bağlantısı başarılı!')
            
            # Auth test
            auth_msg = {
                'type': 'auth',
                'username': USERNAME,
                'password': PASSWORD
            }
            await websocket.send(json.dumps(auth_msg))
            print('📤 Auth mesajı gönderildi')
            
            response = await websocket.recv()
            print(f'📥 Response: {response}')
            
            print('✅ Test başarılı!')
            
    except Exception as e:
        print(f'❌ Test hatası: {e}')

if __name__ == "__main__":
    print("🚀 Generate Makinası WebSocket Client")
    print("=" * 50)
    print(f"🌐 Server: {WEBSOCKET_URL}")
    print(f"👤 Username: {USERNAME}")
    print(f"🔐 Password: {PASSWORD}")
    print("=" * 50)
    
    if SERVER_IP == "YOUR_SERVER_IP":
        print("⚠️  UYARI: SERVER_IP'yi gerçek IP adresi ile değiştirin!")
        print("📝 Örnekler:")
        print("   SERVER_IP = 'propai.store'  # Domain adı")
        print("   SERVER_IP = '192.168.1.100'  # Yerel ağ IP'si")
        print("   SERVER_IP = '46.xxx.xxx.xxx'  # Dış IP adresi")
        exit(1)
    
    print("1. Test bağlantısı için 't' yazın")
    print("2. Sürekli çalıştırmak için 'r' yazın")
    print("3. Çıkmak için 'q' yazın")
    
    choice = input("Seçiminiz: ").lower().strip()
    
    if choice == 't':
        print("\n🧪 Test bağlantısı başlatılıyor...")
        asyncio.run(test_websocket_simple())
    elif choice == 'r':
        print("\n🔄 Sürekli client başlatılıyor...")
        print("Durdurmak için Ctrl+C'ye basın")
        try:
            asyncio.run(generate_machine_client())
        except KeyboardInterrupt:
            print("\n⏹️  Client durduruldu")
    elif choice == 'q':
        print("👋 Çıkılıyor...")
    else:
        print("❌ Geçersiz seçim!")
