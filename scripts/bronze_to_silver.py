"""Clean and deduplicate Bronze customer orders into Silver tables."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def transform(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS silver_customer_orders;
            CREATE TABLE silver_customer_orders AS
            SELECT
                order_id,
                date(order_date) AS order_date,
                customer_id,
                trim(customer_name) AS customer_name,
                lower(trim(customer_email)) AS customer_email,
                trim(customer_phone) AS customer_phone,
                product_id,
                trim(product_name) AS product_name,
                trim(category) AS category,
                CAST(quantity AS INTEGER) AS quantity,
                CAST(unit_price AS NUMERIC) AS unit_price,
                CAST(discount_pct AS NUMERIC) AS discount_pct,
                trim(payment_method) AS payment_method,
                trim(shipping_status) AS shipping_status,
                trim(province) AS province,
                CAST(total_amount AS NUMERIC) AS total_amount,
                source_file,
                extracted_at
            FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY order_id ORDER BY source_file, bronze_id
                ) AS row_number
                FROM bronze_customer_orders
                WHERE NULLIF(trim(order_id), '') IS NOT NULL
            )
            WHERE row_number = 1;

            CREATE INDEX idx_silver_orders_date
                ON silver_customer_orders(order_date);
            CREATE INDEX idx_silver_orders_customer
                ON silver_customer_orders(customer_id);
            """
        )
        total = connection.execute("SELECT COUNT(*) FROM silver_customer_orders").fetchone()[0]
    print(f"silver_customer_orders: {total:,} deduplicated rows -> {database}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/warehouse.db"))
    args = parser.parse_args()
    transform(args.database)


if __name__ == "__main__":
    main()