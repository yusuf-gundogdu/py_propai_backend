# 1. Proje dizinine git
cd ~/Desktop/fastapi

# 2. Sanal ortam oluştur (Python 3.7+ gerektirir)
python -m venv venv

# 3. Sanal ortamı aktif et
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Gereksinimleri YÜKLE (requirements.txt varsa)
pip install --upgrade pip
pip install -r requirements.txt

# 5. PostgreSQL bağlantısını kontrol et (Mac için)
brew services start postgresql@14

# 6. Veri Tabanı ayarları Mac için
bash
brew install postgresql@14
brew services start postgresql@14

# 7. PostgreSQL veri tabanı oluşturma ve kullanıcı ayarları
bash
sudo -u postgres psql -c "CREATE DATABASE fastapi_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'SIFRE ENV DOSYASI ICINDE YAZIYOR';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fastapi_db TO postgres;"

# 8. FastAPI uygulamasını başlat
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes -out certs/fullchain.pem -keyout certs/privkey.pem -days 365 -subj "/CN=localhost"

# 9. FastAPI uygulamasını başlat (SSL sertifikası ile)
uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-certfile=certs/fullchain.pem --ssl-keyfile=certs/privkey.pem
sudo uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-certfile=certs/fullchain.pem --ssl-keyfile=certs/privkey.pem
