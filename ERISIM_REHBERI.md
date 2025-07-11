# PropAI Admin Paneli Erişim Rehberi

## 🚀 Hızlı Başlangıç

### 1. Uygulamayı Başlatın
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Tarayıcıda Açın
```
http://localhost:8000
```

## 📍 Erişim Noktaları

### 🏠 Ana Sayfa
- **URL**: `http://localhost:8000/`
- **Açıklama**: PropAI platformunun ana sayfası
- **Özellikler**: 
  - Platform tanıtımı
  - API dokümantasyon linki
  - Admin panel linki

### 🔐 Admin Paneli Giriş
- **URL**: `http://localhost:8000/admin/`
- **Açıklama**: Admin paneline giriş sayfası
- **Giriş Bilgileri**: 
  - Kullanıcı adı: `admin` (veya .env dosyasındaki BASIC_AUTH_USERNAME)
  - Şifre: .env dosyasındaki BASIC_AUTH_PASSWORD

### 📊 Admin Dashboard
- **URL**: `http://localhost:8000/admin/dashboard`
- **Açıklama**: Ana yönetim paneli
- **Özellikler**:
  - Sistem istatistikleri
  - Grafikler
  - Hızlı işlem butonları

## 🗂️ Admin Panel Menüleri

### 👥 Kullanıcı Yönetimi
- **URL**: `http://localhost:8000/admin/users`
- **Özellikler**:
  - Kullanıcı listesi
  - Yeni kullanıcı ekleme
  - Kullanıcı düzenleme
  - Kullanıcı silme

### 💳 Hesap Yönetimi
- **URL**: `http://localhost:8000/admin/accounts`
- **Özellikler**:
  - Hesap listesi
  - UDID/Platform filtreleme
  - Hesap ekleme/düzenleme/silme

### 🧠 Model Yönetimi
- **URL**: `http://localhost:8000/admin/models`
- **Özellikler**:
  - AI model listesi
  - Model istatistikleri
  - Model ekleme/düzenleme/silme

### 🖼️ Resim Yönetimi
- **URL**: `http://localhost:8000/admin/images`
- **Özellikler**:
  - Resim listesi
  - Prompt/durum filtreleme
  - Resim detayları ve indirme

### 📚 API Dokümantasyon
- **URL**: `http://localhost:8000/admin/api-docs`
- **Özellikler**:
  - API endpoint listesi
  - API test aracı
  - Swagger UI linkleri

## 🔗 API Dokümantasyon

### Swagger UI
- **URL**: `http://localhost:8000/docs`
- **Açıklama**: İnteraktif API dokümantasyonu

### ReDoc
- **URL**: `http://localhost:8000/redoc`
- **Açıklama**: Alternatif API dokümantasyonu

## 🔧 Kurulum ve Yapılandırma

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Veritabanı Ayarları
```bash
# PostgreSQL başlat
brew services start postgresql@14

# Veritabanı oluştur
sudo -u postgres psql -c "CREATE DATABASE fastapi_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fastapi_db TO postgres;"
```

### 3. Çevre Değişkenleri (.env)
```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost/fastapi_db
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
```

## 🛡️ Güvenlik

### Admin Erişimi
- Sadece admin kullanıcıları (ID=1) admin paneline erişebilir
- Cookie tabanlı kimlik doğrulama
- Otomatik oturum sonlandırma

### API Güvenliği
- JWT token tabanlı kimlik doğrulama
- Role-based access control
- Rate limiting (opsiyonel)

## 🚨 Sorun Giderme

### Giriş Yapamıyorum
1. .env dosyasındaki kullanıcı adı ve şifreyi kontrol edin
2. Veritabanı bağlantısını kontrol edin
3. Admin kullanıcısının oluşturulduğundan emin olun

### Sayfa Yüklenmiyor
1. Uygulamanın çalıştığından emin olun
2. Port numarasını kontrol edin
3. Firewall ayarlarını kontrol edin

### Veritabanı Hatası
1. PostgreSQL servisinin çalıştığını kontrol edin
2. Veritabanı bağlantı bilgilerini kontrol edin
3. Tabloların oluşturulduğunu kontrol edin

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Veritabanı bağlantısını test edin
3. Uygulama durumunu kontrol edin

```bash
# Log kontrolü
tail -f logs/app.log

# Veritabanı testi
python -c "from app.database import engine; print('DB OK')"

# Uygulama durumu
curl http://localhost:8000/health
``` 