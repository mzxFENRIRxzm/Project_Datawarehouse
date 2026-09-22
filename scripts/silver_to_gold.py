"""Build a Kimball-style Gold star schema from Silver customer orders."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def build_gold(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS fact_sales;
            DROP TABLE IF EXISTS dim_date;
            DROP TABLE IF EXISTS dim_customer;
            DROP TABLE IF EXISTS dim_product;
            DROP TABLE IF EXISTS dim_payment;

            CREATE TABLE dim_date AS
            SELECT DISTINCT
                CAST(strftime('%Y%m%d', order_date) AS INTEGER) AS date_key,
                order_date AS full_date,
                CAST(strftime('%Y', order_date) AS INTEGER) AS year,
                ((CAST(strftime('%m', order_date) AS INTEGER) - 1) / 3) + 1 AS quarter,
                CAST(strftime('%m', order_date) AS INTEGER) AS month,
                CAST(strftime('%w', order_date) AS INTEGER) IN (0, 6) AS is_weekend
            FROM silver_customer_orders
            WHERE order_date IS NOT NULL;

            CREATE TABLE dim_customer AS
            SELECT
                customer_id AS customer_key,
                customer_name,
                customer_email,
                customer_phone,
                province,
                COUNT(*) AS total_orders,
                ROUND(SUM(total_amount), 2) AS total_spent
            FROM silver_customer_orders
            GROUP BY customer_id, customer_name, customer_email, customer_phone, province;

            CREATE TABLE dim_product AS
            SELECT
                product_id AS product_key,
                product_name,
                category,
                MAX(unit_price) AS current_price
            FROM silver_customer_orders
            GROUP BY product_id, product_name, category;

            CREATE TABLE dim_payment AS
            SELECT DISTINCT
                payment_method AS payment_key,
                payment_method
            FROM silver_customer_orders;

            CREATE TABLE fact_sales AS
            SELECT
                ROW_NUMBER() OVER (ORDER BY order_id, product_id) AS sale_key,
                CAST(strftime('%Y%m%d', order_date) AS INTEGER) AS date_key,
                order_id,
                product_id AS product_key,
                customer_id AS customer_key,
                payment_method AS payment_key,
                quantity,
                unit_price,
                ROUND(quantity * unit_price, 2) AS line_total,
                ROUND(quantity * unit_price * discount_pct / 100.0, 2) AS discount_amount,
                ROUND(total_amount, 2) AS net_revenue,
                shipping_status
            FROM silver_customer_orders;

            CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
            CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
            CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
            """
        )
        for table in ("dim_date", "dim_customer", "dim_product", "dim_payment", "fact_sales"):
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count:,} rows")
    print(f"gold schema built -> {database}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/warehouse.db"))
    args = parser.parse_args()
    build_gold(args.database)


if __name__ == "__main__":
    main()