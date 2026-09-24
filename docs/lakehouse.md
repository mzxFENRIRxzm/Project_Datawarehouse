# Open source lakehouse and Featured Charts

The integration uses the five Northwind Thailand files supplied in `project.zip`.
`scripts/import_project.py` copies those exact files into
`data/landing/northwind_thai_large_data/` and refuses to replace a different
existing file. No generated replacement dataset is required.

```text
project/northwind_thai_large_data (CSV, JSON, XLSX, TXT, DOCX)
      | import_project.py
      v
data/landing/northwind_thai_large_data
      | northwind_lakehouse.py
      +--> MinIO: warehouse/bronze/northwind/<content hash>/ (original files)
      +--> PostgreSQL: northwind_stage_<hash> (typed staging, not BI)
                    | Trino PostgreSQL connector
                    v
             Iceberg: northwind_silver_<hash>
                    | Trino SQL transforms
                    v
             Iceberg: northwind_gold_<hash> (Parquet on MinIO)
                    | validated publication view
                    v
             iceberg.northwind_gold.sales_dashboard
                    | Superset Trino connector
                    v
             Featured Charts (6 charts)
```

## Run on Windows PowerShell

Run these commands from `Project_Datawarehouse`. Docker Desktop and Compose v2
must be running.

```powershell
python scripts/import_project.py 'C:\Users\User\Downloads\project'
python scripts/init_environment.py
docker compose config --quiet
docker compose up -d lakehouse-trino
docker compose run --rm --build northwind-etl
docker compose up -d --build superset
docker compose exec superset /app/.venv/bin/python /app/pythonpath/bootstrap_dashboard.py
```

Open `http://localhost:8088/superset/dashboard/featured-charts/` and sign in
with `SUPERSET_ADMIN_USERNAME` and `SUPERSET_ADMIN_PASSWORD` from the private
`.env`. Do not commit `.env`. The script creates `.env` only once and generates
random values. If this repository is being attached to **already running**
PostgreSQL/MinIO volumes that predate `.env`, run
`python scripts/init_environment.py --use-running-credentials` before Compose;
this reads the existing credentials without printing them.

On subsequent loads, run `docker compose run --rm northwind-etl`. The
content hash prevents duplicate rows on retries. New source content creates
new Iceberg schemas, and the stable dashboard view is switched only after
counts and net revenue reconcile. Previously published tables are retained
as snapshots, so manage old batches deliberately if storage grows.

`fact_sales` has one row per order detail. Revenue is
`quantity * UnitPrice * (1 - Discount)` with the file's discount fraction
and two decimal rounding. The DOCX policy's 7% freight VAT is applied once
per order in `fact_orders.freight_including_vat`, so it is not multiplied by
the number of line items. Contact names and phone numbers remain
in the original raw files; analytics only publishes customer ID, company, and
city. MinIO, Hive Metastore, Trino, and Superset host ports bind to localhost.

The supplied SQLite `silver.db` and `gold.db` are reference outputs. This
pipeline rebuilds the model into actual Iceberg tables to make Superset query
the open source lakehouse. The existing `suphasan_daily_etl` DAG has no
Northwind work; the command above triggers this separate Northwind pipeline.

## Verification

```powershell
python -m unittest discover -s tests -v
docker compose run --rm northwind-etl --validate-only
docker compose ps
```

Check the printed `source_counts`, `sales_lines`, and `net_revenue` after a
full run. Superset's dashboard uses Trino's `iceberg.northwind_gold.sales_dashboard`
view; the saved charts can be edited in Superset after bootstrap.

For an API check and a dashboard screenshot on Windows with Microsoft Edge:

```powershell
python scripts/check_featured_charts.py
python -m pip install playwright
python scripts/capture_featured_charts.py
```

The screenshot is saved at [`featured-charts.png`](featured-charts.png).

Versions used by the integration: PostgreSQL 16, Hive Metastore 4.0.0,
Trino 438, and Superset 5.0.0. Docker image tags and Python dependencies
are declared in the repository. The pipeline is suited for this supplied
10,000-row demonstration; PostgreSQL staging, full reloads, and retained
batches would need retention and access controls for a production data lake.
