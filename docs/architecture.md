# Suphasan Data Warehouse Architecture

## Overview

The project uses a local Medallion pipeline for the multi-format
`customer_orders` landing set:

```text
Landing files (CSV, JSON, JSONL, XLSX, DOCX)
        |
        v
Bronze SQLite: raw rows + source metadata
        |
        v
Silver SQLite: typed, cleaned, deduplicated orders
        |
        v
Gold SQLite: Kimball star schema
        |
        v
Superset or SQL clients
```

## Gold Grain

`fact_sales` has one row per product line in an order. A single `order_id`
may therefore appear multiple times when an order contains multiple products.

## Pipeline Commands

```bash
python scripts/raw_to_bronze.py
python scripts/bronze_to_silver.py
python scripts/silver_to_gold.py
```

The default database is `data/warehouse/warehouse.db`. The model definition is
available in [star_schema.dbml](star_schema.dbml).

## Runtime Services

Docker Compose runs Django, PostgreSQL, Redis, Airflow, Superset, and Nginx.
There is no external OLAP database dependency. Django and metadata services use
PostgreSQL; the local Gold model is SQLite for portable development and tests.
