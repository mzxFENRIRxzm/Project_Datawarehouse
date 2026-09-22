"""Generate Thai customer-order sample data for the landing zone.

The same records are written to CSV, JSON, JSONL text, XLSX, and DOCX so
each source format can be exercised through the Bronze ingestion layer.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from faker import Faker
from openpyxl import Workbook
from docx import Document


FIELDS = [
    "order_id", "order_date", "customer_id", "customer_name", "customer_email",
    "customer_phone", "product_id", "product_name", "category", "quantity",
    "unit_price", "discount_pct", "payment_method", "shipping_status", "province",
    "total_amount",
]

PRODUCTS = [
    ("P001", "ข้าวหอมมะลิ 5 กก.", "อาหารแห้ง", 185.00),
    ("P002", "น้ำมันปาล์ม 1 ลิตร", "เครื่องปรุง", 48.00),
    ("P003", "กาแฟคั่วบด 250 กรัม", "เครื่องดื่ม", 129.00),
    ("P004", "เสื้อยืดผ้าฝ้าย", "แฟชั่น", 299.00),
    ("P005", "กระเป๋าผ้าแคนวาส", "แฟชั่น", 159.00),
    ("P006", "แก้วน้ำสเตนเลส", "ของใช้ในบ้าน", 249.00),
    ("P007", "หูฟังไร้สาย", "อิเล็กทรอนิกส์", 799.00),
    ("P008", "สายชาร์จ USB-C", "อิเล็กทรอนิกส์", 199.00),
    ("P009", "สมุดโน้ตปกแข็ง", "เครื่องเขียน", 89.00),
    ("P010", "ปากกาลูกลื่นสีน้ำเงิน", "เครื่องเขียน", 25.00),
]
PAYMENT_METHODS = ["โอนเงิน", "บัตรเครดิต", "เก็บเงินปลายทาง", "e-Wallet"]
SHIPPING_STATUSES = ["จัดส่งแล้ว", "กำลังจัดส่ง", "รอดำเนินการ", "ส่งสำเร็จ"]


def generate_records(count: int, seed: int) -> list[dict[str, Any]]:
    """Create deterministic records containing Thai customer identities."""
    if count < 1:
        raise ValueError("count must be at least 1")

    fake = Faker("th_TH")
    Faker.seed(seed)
    random.seed(seed)
    start_date = date.today() - timedelta(days=365)
    records: list[dict[str, Any]] = []

    for index in range(1, count + 1):
        product_id, product_name, category, unit_price = random.choice(PRODUCTS)
        quantity = random.randint(1, 5)
        discount_pct = random.choice([0, 0, 0, 5, 10, 15])
        total_amount = round(quantity * unit_price * (1 - discount_pct / 100), 2)
        records.append(
            {
                "order_id": f"ORD{index:08d}",
                "order_date": fake.date_between(start_date=start_date, end_date="today").isoformat(),
                "customer_id": f"CUS{index:08d}",
                "customer_name": fake.name(),
                "customer_email": fake.email(),
                "customer_phone": fake.phone_number(),
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_pct": discount_pct,
                "payment_method": random.choice(PAYMENT_METHODS),
                "shipping_status": random.choice(SHIPPING_STATUSES),
                "province": fake.province(),
                "total_amount": total_amount,
            }
        )
    return records


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)


def write_json(records: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_xlsx(records: list[dict[str, Any]], path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "customer_orders"
    sheet.append(FIELDS)
    for record in records:
        sheet.append([record[field] for field in FIELDS])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    workbook.save(path)


def write_docx(records: list[dict[str, Any]], path: Path) -> None:
    document = Document()
    document.add_heading("Customer Orders", level=1)
    document.add_paragraph(f"Generated records: {len(records):,}")
    table = document.add_table(rows=1, cols=len(FIELDS))
    table.style = "Table Grid"
    for cell, field in zip(table.rows[0].cells, FIELDS):
        cell.text = field
    for record in records:
        cells = table.add_row().cells
        for cell, field in zip(cells, FIELDS):
            cell.text = str(record[field])
    document.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=10_000, help="records per output file")
    parser.add_argument("--seed", type=int, default=20260922, help="random seed")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/landing/customer_orders"),
        help="Bronze landing directory",
    )
    args = parser.parse_args()

    records = generate_records(args.records, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    writers = {
        "customer_orders.csv": write_csv,
        "customer_orders.json": write_json,
        "customer_orders.txt": write_text,
        "customer_orders.xlsx": write_xlsx,
        "customer_orders.docx": write_docx,
    }
    for filename, writer in writers.items():
        writer(records, args.output_dir / filename)
        print(f"created {args.output_dir / filename} ({len(records):,} records)")


if __name__ == "__main__":
    main()