# Decorator AI

Decorator AI, kullanıcıların oda fotoğrafı üzerinden kişiselleştirilmiş iç mimari tasarım önerileri almasını sağlayan AI destekli bir mobil uygulamadır. Kullanıcı bir oda fotoğrafı yükler, tasarım tercihlerini belirler ve sistem bu tercihlere uygun oda tasarımları ile eşleşen mobilya ürünlerini önerir.

Şu anda sistem **salon** ve **mutfak** tasarımlarını desteklemektedir.

## Uygulama Demosu

Android uygulaması APK olarak paylaşılmıştır. Doğrudan indirip apk ile yükleyerek demoya erişebilirsiniz, ek herhangi bir kurulum adımı gerekmiyor:

https://drive.google.com/drive/folders/1qfPt-woVqL0-qeMfMBRF-1lSwGDh_ePu


## Sistem Bileşenleri

```text
┌──────────────────────────────┐
│ Kullanıcı (Android)          │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Flutter Android App          │
│ - Room scan flow             │
│ - AI design suggestions      │
│ - Product hotspots           │
└───────────────┬──────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────────┐   ┌──────────────────────────────┐
│ Firebase         │   │ FastAPI Backend Server       │
│ Auth + Firestore │   │ - API layer                  │
│                  │   │ - Job yönetimi               │
└──────────────────┘   │ - Agentic AI pipeline        │
                       └───────┬────────┬───────┬─────┘
                               │        │       │
                               ▼        ▼       ▼
                    ┌──────────────┐ ┌────────┐ ┌─────────────────────┐
                    │ PostgreSQL   │ │ Redis  │ │ Qdrant Vector DB    │
                    │ Ürün verisi  │ │ + RQ   │ │ Vector search / RAG │
                    └──────┬───────┘ └────────┘ └───────────┬─────────┘
                           │                                │
                           └──────────────┬─────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ Cloud Vertex AI        │
                              │ AI ve embedding üretimi│
                              └───────────┬────────────┘
                                          ▲
                                          │
                              ┌───────────┴────────────┐
                              │ Data Crawler           │
                              │ + Preprocessor         │
                              │ + Enrichment Pipeline  │
                              └────────────────────────┘
```

Temel proje parçaları:

- `flutter-app/`: Flutter ile geliştirilmiş Android mobil uygulaması.
- `ai-service/`: Backend API, job sistemi, AI workflow, database erişimi ve ürün arama servisleri.
- `data/`: Ürün crawler’ları, ürün preprocessing adımları ve enrichment pipeline.
- Firebase: Authentication ve kullanıcıya gösterilen bulut verilerinin yönetimi.
- Google Cloud Vertex AI: Gemini modelleri ve embedding modelleri.

## Mimari

### Firebase

Firebase, client tarafında authentication ve kullanıcıya ait uygulama verilerinin saklanması için kullanılır.

- Firebase Auth, kullanıcı girişi ve guest user akışlarını yönetir.
- Firestore; curated design’lar, kaydedilmiş veya oluşturulmuş tasarımlar, favoriler ve product hotspot verileri gibi kullanıcıya gösterilen verileri saklar.
- Uygulama Vertex AI’a doğrudan istek atmaz. AI işlemleri backend üzerinden yürütülür.

### Backend

Sistem, server-client mimarisiyle çalışır.

Flutter uygulaması oda fotoğraflarını ve tasarım isteklerini FastAPI backend’e gönderir. Backend bu istek için bir design job oluşturur, uzun süren AI işlemlerini kuyruğa alır, job durumunu takip eder, sonuçları saklar ve tamamlanan tasarımı uygulamaya döner.

Backend tarafında kullanılan ana teknolojiler:

- FastAPI
- Python
- PostgreSQL
- Redis
- RQ workers
- Qdrant
- LangGraph
- Docker Compose

### Agentic AI Pipeline

Backend, her design job için agentic AI pipeline çalıştırır.

Pipeline temel olarak şu adımlardan oluşur:

1. Kullanıcı isteğini doğrular.
2. Oda fotoğrafını analiz eder.
3. Tasarım stratejileri oluşturur.
4. RAG ile uygun mobilya adaylarını getirir.
5. Ürün verisi ve vector search için PostgreSQL ile Qdrant kullanır.
6. Ürünleri yeniden sıralar.
7. Mobilya yerleşim planını oluşturur.
8. Nihai oda görsellerini üretir veya compose eder.
9. Sonucu doğrular ve kaydeder.

AI workflow; LangGraph stage’leri, structured output’lar, tool-like retrieval adımları, multimodal oda/ürün girdileri ve Vertex AI modelleri üzerine kuruludur.

### Data Pipeline

Data pipeline, backend tarafından kullanılan ürün kataloğunu oluşturur.

- Scrapy crawler’ları kaynak mağazalardan mobilya ürünlerini toplar.
- Raw data JSONL formatında saklanır.
- Preprocessor, ürünleri normalize eder ve Vertex Gemini veya fallback rule’lar ile zenginleştirir.
- Backend, enriched ürünleri PostgreSQL’e import eder.
- Backend indexing script’leri Vertex text/image embedding’leri üretir ve vector’leri Qdrant’a yazar.

Data pipeline tarafında kullanılan ana teknolojiler:

- Scrapy
- Python
- JSONL
- Vertex Gemini
- Vertex text ve multimodal embeddings
- PostgreSQL
- Qdrant

### Frontend

Frontend, Android odaklı bir Flutter uygulamasıdır.

Uygulamada yer alan başlıca özellikler:

- Room scan flow
- AI design suggestions
- Generated design detail screen’leri
- Product hotspot’ları
- Favorites
- Profile settings
- Backend URL configuration
- Local ve push notification desteği

Tasarım dili; sıcak, mobil öncelikli ve Material 3 tabanlı bir iç mimari arayüz üzerine kuruludur.

## Kurulum

### 1. Gereksinimler

Aşağıdaki araçların kurulu olması gerekir:

- Git
- Docker ve Docker Compose
- Python 3.11+
- Flutter SDK
- Android Studio / Android SDK
- Firebase CLI
- FlutterFire CLI
- Google Cloud CLI

Ayrıca şunlara ihtiyaç vardır:

- Firebase project
- Google Cloud project
- Vertex AI etkinleştirilmiş bir Google Cloud ortamı
- Vertex AI için service account JSON key

### 2. Repository’yi Klonlama

```bash
git clone https://github.com/ElifSeden/VisionSpace.git decorator-ai
cd decorator-ai
```

### 3. Data Pipeline Kurulumu

```bash
cd data
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Gerekli `.env` dosyasını örnek dosyadan veya sistem dokümantasyonundan oluşturun. Google service account key dosyasını (genellikle gcp-service-account.json) Git’e eklenmeyen lokal bir `secrets/` klasörüne yerleştirin.

Crawler’ları çalıştırmak için:

```bash
python scraping.py --spider vivense --target-per-category 50
python crawler/run_all.py
```

Preprocessing adımını çalıştırmak için:

```bash
python preprocessor/run.py
```

### 4. Backend Kurulumu

```bash
cd ../ai-service
cp .env.example .env
```

`.env` dosyasını PostgreSQL, Redis, Qdrant, Vertex AI, image storage ve service account path değerlerine göre düzenleyin.

Backend’i başlatmak için:

```bash
make setup
```

Health check:

```bash
curl http://localhost:8000/health
```

Enriched ürünleri import etmek ve vector index oluşturmak için:

```bash
make import-enriched
make index-products
```

API dokümantasyonu aşağıdaki adreslerden erişilebilir:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### 5. Firebase Kurulumu

```bash
cd ../flutter-app
flutterfire configure
firebase deploy --only firestore
```

Uygulamanın kullandığı Firebase Auth provider’larını etkinleştirin. Guest user’ların generated design kaydedebilmesi isteniyorsa anonymous auth da aktif edilmelidir.

### 6. Android Uygulamasını Çalıştırma

```bash
flutter pub get
flutter gen-l10n
```

Android emulator üzerinde çalıştırmak için:

```bash
flutter run --dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000
```

Gerçek bir backend sunucusu ile çalıştırmak için (backend-url kısmını sunucu IP/URL ile değiştirin):

```bash
flutter run --dart-define=BACKEND_BASE_URL=https://backend-url
```

APK build almak için (backend-url kısmını sunucu IP/URL ile değiştirin):

```bash
flutter build apk --dart-define=BACKEND_BASE_URL=https://backend-url
```

## Notlar ve Kısıtlar

- Sistem şu anda yalnızca salon ve mutfak tasarımlarını destekler.
- AI çıktıları tamamen deterministik değildir; sonuçlar modele, görsel girdiye ve kullanıcı tercihine göre değişebilir.
- Ürün dataset’i, AI ve embedding maliyetlerini kontrol altında tutmak için bilinçli olarak sınırlı tutulmuştur.
