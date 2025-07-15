# 🚢 Shipping Data Product

A robust end-to-end data product for ingesting, processing, transforming, and serving insights from **Telegram channel data** — with a particular focus on **object detection** in shared images using **YOLOv8**, and serving analytical insights via a **FastAPI** API.

---

## 📌 Project Overview

The goal is to build a modular and scalable data pipeline that:

- 📥 **Ingests** Telegram messages and media (images)
- 🧠 **Analyzes** images using YOLOv8 object detection
- 🔄 **Transforms** raw data into clean, analytical tables using **dbt**
- 🌐 **Exposes** insights through a high-performance **FastAPI** layer

---

## 🧰 Technologies Used

- **Python 3.x** – Core language
- **FastAPI** – For building the analytical API
- **Uvicorn** – ASGI server for FastAPI
- **Psycopg2** – PostgreSQL database adapter
- **PostgreSQL** – Data warehouse for raw and transformed data
- **Docker & Docker Compose** – Environment and service management
- **dbt** – Data transformation and testing
- **Ultralytics YOLOv8** – Deep learning model for image object detection
- **python-dotenv** – Environment variable management

---

## 📁 Project Structure

```
shipping-data-product/
├── telegram_data_dbt/           # dbt project for transformations
│   ├── models/
│   │   ├── staging/             # Raw → Clean (e.g., stg_image_detections.sql)
│   │   └── marts/               # Final data marts (e.g., fct_messages.sql)
│   ├── profiles.yml             # DB connection profile
│   ├── packages.yml             # dbt package dependencies
│   └── sources.yml              # Raw source table definitions
├── scripts/                     # Python scripts for ingestion & detection
│   ├── data_loader.py           # [Conceptual] Telegram message ingestion
│   ├── yolo_detector.py         # YOLO detection + DB loader
│   └── data/
│       └── raw/
│           ├── telegram_media/    # Raw image lake
│           └── telegram_messages/ # Raw Telegram message files
│       └── processed/
├── my_project/                  # FastAPI app
│   ├── main.py                  # Entry point for FastAPI
│   ├── database.py              # DB connection logic
│   ├── schemas.py               # Pydantic request/response models
│   ├── crud.py                  # DB query logic
│   └── models.py                # [Optional] ORM models
├── .env                         # Secrets & config (ignored by Git)
├── docker-compose.yml           # Service definitions
└── README.md                    # You're reading this!
```

---

## ✅ Features Implemented

### 1. 🔄 Data Ingestion & Object Detection
- **YOLOv8 Image Detection**:
  - Detects objects in raw images using `yolo_detector.py`
  - Auto-skips previously processed images
  - Saves detections (class, confidence, bounding box) to `raw.image_detections` table
  - Includes dummy image generation for testing

### 2. 🔁 Data Transformation with dbt
- **Source Models**: Recognize raw tables like `raw.telegram_messages`, `raw.image_detections`
- **Staging Models**:
  - `stg_image_detections.sql`: Cleaned version of detection results
  - `stg_image_detections.yml`: Metadata and tests (e.g., `not_null`, `unique`, `dbt_utils.at_least_one`)
- **Marts**:
  - Fact and dimension models like `fct_messages` and `dim_channels`

### 3. 🌐 Analytical API (FastAPI)
- **Core Structure**:
  - `main.py`: FastAPI router
  - `crud.py`: Query logic using raw SQL
  - `schemas.py`: Validated data responses with Pydantic
- **Implemented Endpoints**:
  - `GET /api/reports/top-products?limit=10`  
    → Top frequently mentioned “products” from Telegram messages
  - `GET /api/channels/{channel_name}/activity`  
    → Message activity per day for a given channel
  - `GET /api/search/messages?query=keyword`  
    → Full-text search across messages

---

## 🚀 How to Run & Test

### 1. 🧪 Environment Setup

- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- Create a `.env` file:
  ```env
  POSTGRES_DB=your_db
  POSTGRES_USER=your_user
  POSTGRES_PASSWORD=your_password
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  TELEGRAM_API_ID=your_api_id
  TELEGRAM_API_HASH=your_api_hash
  ```

### 2. 🐳 Run with Docker

```bash
docker-compose up --build
```

- This will:
  - Launch PostgreSQL
  - Run YOLO object detection
  - Start the FastAPI server

### 3. 🏗️ Build dbt Models

```bash
cd telegram_data_dbt
dbt deps
dbt build
```

### 4. 🧪 Test the API

- Open [http://localhost:8000/docs](http://localhost:8000/docs) to access Swagger UI.

- Try:
  - `GET /api/reports/top-products?limit=5`
  - `GET /api/channels/chemed_channel/activity`
  - `GET /api/search/messages?query=paracetamol`

---

## 🔮 Next Steps

- ✅ Implement real `data_loader.py` for Telegram scraping
- 🔍 Improve product recognition using NLP / keyword extraction
- 🧠 Add more dbt marts (e.g., `fct_image_detections_aggregated`)
- 🔐 Add API auth (JWT, OAuth)
- 🔄 CI/CD pipelines (GitHub Actions, etc.)
- 📊 Integrate BI tools like Metabase or Apache Superset

---

## 🛡️ Security Notice

> ⚠️ If you accidentally pushed `.env` to GitHub, remove it from version history and rotate any credentials it contained.

---

## 📬 Contact

For questions, contributions, or issues, feel free to open an issue or reach out.
