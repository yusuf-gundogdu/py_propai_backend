

import asyncio
import websockets
import logging
import os
from dotenv import load_dotenv
from aiohttp import web
import json
from datetime import datetime, timezone

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
USERNAME = os.getenv("WS_USERNAME")
PASSWORD = os.getenv("WS_PASSWORD")

logging.basicConfig(level=logging.INFO, format="[WS] %(message)s")

connected_clients = set()

async def authenticate(websocket):
    await websocket.send("AUTH: Kullanıcı adı:")
    username = await websocket.recv()
    await websocket.send("AUTH: Şifre:")
    password = await websocket.recv()
    if username == USERNAME and password == PASSWORD:
        await websocket.send("AUTH_OK")
        return True
    else:
        await websocket.send("AUTH_FAIL")
        return False

async def handler(websocket):
    peer = websocket.remote_address
    logging.info(f"Bağlantı denemesi: {peer}")
    if not await authenticate(websocket):
        logging.info(f"Hatalı giriş: {peer}")
        await websocket.close()
        return
    connected_clients.add(websocket)
    logging.info(f"Bağlandı: {peer}")
    try:
        async for message in websocket:
            logging.info(f"{peer} mesaj gönderdi: {message}")
            await websocket.send(f"ALINDI: {message}")
    except Exception as e:
        logging.info(f"Bağlantı koptu: {peer} ({e})")
    finally:
        connected_clients.discard(websocket)
        logging.info(f"Ayrıldı: {peer}")


import json
from datetime import datetime, timezone


async def broadcast_json(payload):
    if connected_clients:
        for ws in list(connected_clients):
            try:
                await ws.send(json.dumps(payload))
            except Exception as e:
                logging.info(f"[WS] Broadcast mesajı gönderilemedi: {e}")

# --- HTTP Broadcast API (aiohttp) ---
async def handle_broadcast(request):
    try:
        payload = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")
    asyncio.create_task(broadcast_json(payload))
    return web.Response(text="OK")

async def start_http_api():
    app = web.Application()
    app.router.add_post('/', handle_broadcast)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8876)
    await site.start()
    logging.info("[WS] Broadcast API HTTP sunucu başlatıldı (port 8876)")

async def broadcast_test_message():
    while True:
        if connected_clients:
            test_payload = {"action": "test_json"}
            await broadcast_json(test_payload)
        await asyncio.sleep(5)

def start_broadcast_api():
    from ws.broadcast_api import start_broadcast_api_in_thread
    start_broadcast_api_in_thread()

async def main():
    # Broadcast HTTP API'yi başlat (aynı event loop'ta)
    await start_http_api()
    async with websockets.serve(handler, "0.0.0.0", 8765):
        logging.info("WS sunucu başlatıldı (port 8765)")
        # Test mesajı gönderen task başlat
        asyncio.create_task(broadcast_test_message())
        await asyncio.Future()  # sonsuza kadar çalış

if __name__ == "__main__":
    asyncio.run(main())
