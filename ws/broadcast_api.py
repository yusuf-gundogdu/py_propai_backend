from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from datetime import datetime, timezone

# Bu modül ws/server.py tarafından import edilecek
# ws/server.py içindeki connected_clients setine erişim için
import ws.server as ws_server

class BroadcastHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            payload = json.loads(post_data)
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return
        # Mesajı tüm bağlı clientlara broadcast et
        loop = ws_server.asyncio.get_event_loop()
        loop.create_task(ws_server.broadcast_json(payload))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_broadcast_api():
    server = HTTPServer(('0.0.0.0', 8876), BroadcastHandler)
    print('[WS] Broadcast API HTTP sunucu baslatildi (port 8876)')
    server.serve_forever()

def start_broadcast_api_in_thread():
    t = threading.Thread(target=run_broadcast_api, daemon=True)
    t.start()
