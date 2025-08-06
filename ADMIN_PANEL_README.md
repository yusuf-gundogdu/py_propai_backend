# PropAI Admin Panel

Bu dokümantasyon, PropAI FastAPI uygulaması için oluşturulan JHipster benzeri admin management panelini açıklar.

## Özellikler

### 🎯 Ana Dashboard
- **Genel İstatistikler**: Kullanıcı, hesap, model ve resim sayıları
- **Grafikler**: Son 7 gün resim oluşturma aktivitesi
- **Sistem Durumu**: API sunucusu, veritabanı ve AI modelleri durumu
- **Hızlı İşlemler**: Diğer sayfalara hızlı erişim

### 👥 Kullanıcı Yönetimi
- **Kullanıcı Listesi**: Tüm kullanıcıları görüntüleme
- **Kullanıcı Ekleme**: Yeni kullanıcı oluşturma
- **Kullanıcı Düzenleme**: Kullanıcı bilgilerini güncelleme
- **Kullanıcı Silme**: Kullanıcı hesabını silme (admin hariç)

### 💳 Hesap Yönetimi
- **Hesap Listesi**: Tüm hesapları görüntüleme
- **Filtreleme**: UDID ve platform bazında filtreleme
- **Hesap Ekleme**: Yeni hesap oluşturma
- **Hesap Düzenleme**: Hesap bilgilerini güncelleme
- **Hesap Silme**: Hesap silme

### 🧠 Model Yönetimi
- **Model Listesi**: Tüm AI modellerini görüntüleme
- **Model İstatistikleri**: Aktif/pasif model sayıları
- **Model Ekleme**: Yeni model oluşturma
- **Model Düzenleme**: Model bilgilerini güncelleme
- **Model Silme**: Model silme
- **Durum Grafiği**: Model durumlarının görsel gösterimi

### 🖼️ Resim Yönetimi
- **Resim Listesi**: Tüm resimleri görüntüleme
- **Filtreleme**: Prompt ve durum bazında filtreleme
- **Resim Detayları**: Resim bilgilerini ve önizleme
- **Resim İndirme**: Oluşturulan resimleri indirme
- **Resim Silme**: Resim silme
- **Durum Grafiği**: Resim durumlarının görsel gösterimi

### 📚 API Dokümantasyon
- **Endpoint Listesi**: Tüm API endpoint'lerini görüntüleme
- **API İstatistikleri**: HTTP method dağılımı
- **API Tag'leri**: Endpoint kategorileri
- **API Test**: Endpoint'leri test etme aracı
- **Hızlı Linkler**: Swagger UI, ReDoc ve OpenAPI JSON

## Kurulum

### 1. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Admin Paneline Erişim
- **URL**: `http://localhost:8000/admin/`
- **Kimlik Doğrulama**: Admin kullanıcı bilgileri ile giriş yapın

## Kullanım

### Dashboard
Ana sayfa genel sistem durumunu gösterir:
- Toplam kullanıcı, hesap, model ve resim sayıları
- Son 7 gün resim oluşturma grafiği
- Sistem bileşenlerinin durumu

### Kullanıcı Yönetimi
1. **Kullanıcıları Görüntüleme**: `/admin/users` sayfasında tüm kullanıcılar listelenir
2. **Yeni Kullanıcı Ekleme**: "Yeni Kullanıcı" butonuna tıklayarak modal açılır
3. **Kullanıcı Düzenleme**: Düzenleme ikonuna tıklayarak kullanıcı bilgilerini güncelleyin
4. **Kullanıcı Silme**: Silme ikonuna tıklayarak kullanıcıyı silin (admin hariç)

### Hesap Yönetimi
1. **Hesapları Görüntüleme**: `/admin/accounts` sayfasında tüm hesaplar listelenir
2. **Filtreleme**: UDID veya platform bazında filtreleme yapabilirsiniz
3. **Yeni Hesap Ekleme**: "Yeni Hesap" butonuna tıklayarak modal açılır
4. **Hesap Düzenleme**: Düzenleme ikonuna tıklayarak hesap bilgilerini güncelleyin

### Model Yönetimi
1. **Modelleri Görüntüleme**: `/admin/models` sayfasında tüm modeller listelenir
2. **Model İstatistikleri**: Sağ panelde model durumları gösterilir
3. **Yeni Model Ekleme**: "Yeni Model" butonuna tıklayarak modal açılır
4. **Model Düzenleme**: Düzenleme ikonuna tıklayarak model bilgilerini güncelleyin

### Resim Yönetimi
1. **Resimleri Görüntüleme**: `/admin/images` sayfasında tüm resimler listelenir
2. **Filtreleme**: Prompt veya durum bazında filtreleme yapabilirsiniz
3. **Resim Detayları**: Göz ikonuna tıklayarak resim detaylarını görüntüleyin
4. **Resim İndirme**: Detay modalında "İndir" butonuna tıklayın

### API Dokümantasyon
1. **Endpoint'leri Görüntüleme**: `/admin/api-docs` sayfasında tüm endpoint'ler listelenir
2. **API Test**: Endpoint satırına tıklayarak test modalını açın
3. **Swagger UI**: "Swagger UI Aç" butonuna tıklayarak Swagger dokümantasyonuna gidin

## API Endpoint'leri

### Admin Panel Endpoint'leri
- `GET /admin/` - Ana dashboard
- `GET /admin/api/stats` - Dashboard istatistikleri
- `GET /admin/users` - Kullanıcı yönetimi sayfası
- `GET /admin/accounts` - Hesap yönetimi sayfası
- `GET /admin/models` - Model yönetimi sayfası
- `GET /admin/images` - Resim yönetimi sayfası
- `GET /admin/api-docs` - API dokümantasyon sayfası

### Veri Yönetimi Endpoint'leri
- `GET /api/users/` - Kullanıcı listesi
- `POST /api/users/` - Yeni kullanıcı oluştur
- `PUT /api/users/{id}` - Kullanıcı güncelle
- `DELETE /api/users/{id}` - Kullanıcı sil

- `GET /api/account/` - Hesap listesi
- `POST /api/account/` - Yeni hesap oluştur
- `PATCH /api/account/{id}` - Hesap güncelle
- `DELETE /api/account/{id}` - Hesap sil

- `GET /api/generatemodellist/` - Model listesi
- `POST /api/generatemodellist/` - Yeni model oluştur
- `PUT /api/generatemodellist/{id}` - Model güncelle
- `DELETE /api/generatemodellist/{id}` - Model sil

- `GET /api/createimage/` - Resim listesi
- `POST /api/createimage/` - Yeni resim oluştur
- `PUT /api/createimage/{id}` - Resim güncelle
- `DELETE /api/createimage/{id}` - Resim sil

## Güvenlik

- Admin paneli sadece admin kullanıcıları tarafından erişilebilir
- Tüm işlemler kimlik doğrulama gerektirir
- Admin kullanıcısı silinemez
- Tüm API endpoint'leri güvenlik kontrollerine tabidir

## Teknik Detaylar

### Frontend Teknolojileri
- **Bootstrap 5**: UI framework
- **Font Awesome**: İkonlar
- **Chart.js**: Grafikler
- **jQuery**: DOM manipülasyonu
- **Jinja2**: Template engine

### Backend Teknolojileri
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **Pydantic**: Veri doğrulama
- **JWT**: Kimlik doğrulama

### Veritabanı
- **PostgreSQL**: Ana veritabanı
- **Async**: Asenkron veritabanı işlemleri

## Geliştirme

### Yeni Sayfa Ekleme
1. `app/templates/admin/` dizininde yeni template oluşturun
2. `app/routers/admin.py` dosyasına yeni endpoint ekleyin
3. Base template'te sidebar'a yeni link ekleyin

### Yeni Özellik Ekleme
1. İlgili router dosyasına yeni endpoint ekleyin
2. Admin template'inde yeni özelliği implement edin
3. Gerekirse JavaScript fonksiyonları ekleyin

## Sorun Giderme

### Yaygın Sorunlar
1. **Template bulunamadı**: `app/templates/admin/` dizininin var olduğundan emin olun
2. **CSS/JS yüklenmiyor**: CDN linklerinin çalıştığından emin olun
3. **API hataları**: Endpoint'lerin doğru tanımlandığından emin olun

### Log Kontrolü
```bash
# Uygulama loglarını kontrol edin
tail -f logs/app.log

# Veritabanı bağlantısını test edin
python -c "from app.database import engine; print('DB OK')"
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 

