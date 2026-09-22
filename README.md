# Suphasan Data Warehouse

ระบบ Data Warehouse สำหรับแพลตฟอร์ม **Suphasan (สุภสาร)** — ระบบจัดการธุรกิจค้าปลีกแบบครบวงจร

## 🏗️ Architecture

```
                    ┌─────────────┐
                    │   Nginx     │ :80
                    │ (Reverse    │
                    │  Proxy)     │
                    └──┬──┬──┬───┘
                       │  │  │
          ┌────────────┘  │  └────────────┐
          ▼               ▼               ▼
   ┌─────────────┐ ┌───────────┐  ┌────────────┐
   │   Django     │ │  Superset │  │  Airflow   │
   │   :8000      │ │  :8088    │  │  :8080     │
   └──────┬───────┘ └─────┬─────┘  └─────┬──────┘
          │               │              │
          ▼               ▼              ▼
   ┌─────────────┐  ┌──────────────────────────┐
    │ PostgreSQL  │  │    SQLite Gold Model    │
    │   :5432     │  │  Bronze → Silver → Gold │
    │  (OLTP)     │  │   (local analytics)     │
   └─────────────┘  └──────────────────────────┘
          │                       │
          └───────┐      ┌───────┘
                  ▼      ▼
              ┌──────────┐
              │  Redis   │
              │  :6379   │
              └──────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Application | Django 5.x | Web storefront & admin |
| OLTP Database | PostgreSQL 16 | Transactional data |
| Data Pipeline | Python + SQLite | Bronze, Silver, and Gold analytics |
| BI / Dashboards | Apache Superset | Business intelligence |
| ETL Orchestrator | Apache Airflow | Pipeline scheduling |
| Cache / Broker | Redis 7 | Superset cache + Airflow broker |
| Reverse Proxy | Nginx | Traffic routing |
| Containers | Docker Compose | Service orchestration |

### Data Modeling: Medallion Architecture + Kimball Star Schema

```
PostgreSQL (OLTP)
    │
    ▼ [Airflow ETL - Daily 02:00]
    │
    ├── 🥉 Bronze Layer    Raw data as-is from source
    ├── 🥈 Silver Layer    Cleaned, deduplicated, normalized
    └── 🥇 Gold Layer      Star schema (facts + dimensions)
                                │
                                ▼ [Superset Datasets]
                                │
                            📊 Dashboards
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (v24+)
- Docker Compose (v2+)

### 1. Clone & Configure

```bash
git clone https://github.com/mzxFENRIRxzm/Project_Datawarehouse.git
cd Project_Datawarehouse
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start All Services

```bash
docker compose up -d
```

### 2.1 Run Official Apache Superset 6.0.0

หากต้องการรัน Apache Superset จาก official repository แยกจาก stack ของ
โปรเจกต์ ให้ใช้คำสั่งต่อไปนี้ในโฟลเดอร์นอกโปรเจกต์:

```bash
git clone https://github.com/apache/superset superset-official
cd superset-official
git checkout tags/6.0.0
docker compose -f docker-compose-image-tag.yml up
```

ใน workspace นี้ใช้ชื่อโฟลเดอร์ `superset-official` เพื่อไม่ชนกับโฟลเดอร์
`superset/` ซึ่งเป็น configuration ของโปรเจกต์ Suphasan หากต้องการเริ่มแบบ
detached ให้เติม `-d` และ official checkout มีไฟล์ `docker/.env-local` สำหรับ
ข้าม demo data ที่ใช้เวลานาน:

```bash
docker compose -f docker-compose-image-tag.yml up -d
```

คำสั่งนี้เป็น Compose stack แยกต่างหากจาก `docker-compose.yml` ของ Suphasan
และอาจใช้พอร์ตเดียวกับ Superset ในโปรเจกต์ (`8088`) จึงไม่ควรรันสอง stack
พร้อมกัน หากมี container เดิมทำงานอยู่ ให้หยุดก่อนด้วย:

```bash
docker compose down
```

### 3. Access Services

| Service | URL | Default Login |
|---|---|---|
| Django App | http://localhost:8000 | - |
| Superset BI | http://localhost:8088 | admin / admin |
| Airflow ETL | http://localhost:8080 | admin / admin |

### 4. Trigger ETL Pipeline

In Airflow UI (http://localhost:8080):
1. Enable the `suphasan_daily_etl` DAG
2. Click **Trigger DAG** to run manually

## 📁 Project Structure

```
Project_Datawarehouse/
├── docker-compose.yml         # All services orchestration
├── .env                       # Environment variables
├── .env.example               # Template
│
├── app/                       # Django Application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── suphasan/              # Django settings
│
├── dags/                      # Airflow DAGs
│   ├── suphasan_etl.py        # Main ETL pipeline
│   └── sql/
│       ├── bronze/
│       ├── silver/
│       │   └── transform_all.sql
│       └── gold/
│           ├── build_dimensions.sql
│           ├── build_facts.sql
│           └── quality_checks.sql
│
├── superset/                  # Superset Configuration
│   └── superset_config.py
│
├── nginx/                     # Reverse Proxy
│   └── nginx.conf
│
├── postgres/                  # PostgreSQL Init
│   └── init/
│       └── 01_create_databases.sql
│
└── docs/                      # Documentation
    ├── architecture.md
    └── data_dictionary.md
```

## 📊 Gold Layer Schema (Star Schema)

### Fact Tables
| Table | Grain | Key Measures |
|---|---|---|
| `fact_sales` | 1 order line item | quantity, revenue, profit |
| `fact_inventory` | 1 stock movement | change_quantity |
| `fact_stock_snapshot` | 1 product/day | current_qty, days_of_supply |
| `fact_logistics` | 1 shipment | shipping_cost |
| `fact_marketing` | 1 coupon | discount_value, times_used |

### Dimension Tables
| Table | Description |
|---|---|
| `dim_date` | Calendar (Thai + English, fiscal year) |
| `dim_product` | Products (SKU, price, cost, margin) |
| `dim_customer` | Customers (loyalty tier, lifetime value) |
| `dim_carrier` | Logistics carriers |
| `dim_payment` | Payment methods |

## 🔧 Development Commands

### Generate multi-format landing data

เริ่มต้น Medallion ด้วยชุด `customer_orders` เพราะมีทั้งมิติ customer/product และ
ตัวชี้วัดยอดขาย เหมาะสำหรับทำ Silver normalization และ Gold star schema ต่อไป

ติดตั้ง dependency แล้วสร้างข้อมูลภาษาไทย 10,000 รายการต่อไฟล์:

```bash
pip install -r app/requirements.txt
python scripts/generate_multiformat_data.py
```

ไฟล์จะถูกสร้างใน `data/landing/customer_orders/` ได้แก่ CSV, JSON, TXT แบบ
JSONL, XLSX และ DOCX โดยใช้ schema เดียวกันทั้งหมด สามารถเปลี่ยนจำนวนข้อมูลได้:

```bash
python scripts/generate_multiformat_data.py --records 50000 --seed 42
```

ใน Medallion ให้เก็บไฟล์ต้นฉบับเหล่านี้เป็น Bronze แบบ immutable, แปลงชนิดข้อมูล
และกำจัดข้อมูลซ้ำใน Silver, แล้วสร้าง `fact_sales` และ dimensions ที่ต้องใช้ใน
รายงานจาก Gold.

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Reset everything (including data)
docker compose down -v

# Rebuild Django image
docker compose build web

# Access PostgreSQL CLI
docker exec -it suphasan-postgres psql -U suphasan
```

## 👥 Team

สาขาวิชาวิทยาการคอมพิวเตอร์ — มหาวิทยาลัยราชภัฏสุราษฎร์ธานี

## 📄 License

MIT License