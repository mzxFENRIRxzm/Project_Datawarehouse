# Suphasan Data Warehouse — Data Dictionary

## ข้อมูลอ้างอิง (Data Dictionary)

เอกสารนี้อธิบายโครงสร้างข้อมูลทุกตารางในระบบ Data Warehouse ของ Suphasan

---

## 🥉 Bronze Layer (ข้อมูลดิบ)

ข้อมูลดิบที่ถูก extract จาก PostgreSQL โดยไม่มีการแปลงใดๆ

| Table | Source (Django) | Description |
|---|---|---|
| `bronze_products` | `storefront_product` | ข้อมูลสินค้า |
| `bronze_orders` | `storefront_order` | ข้อมูลคำสั่งซื้อ |
| `bronze_order_items` | `storefront_orderitem` | รายการสินค้าในคำสั่งซื้อ |
| `bronze_stock_levels` | `inventory_stocklevel` | ยอดคงเหลือสินค้า |
| `bronze_stock_logs` | `inventory_stocklog` | ประวัติการเคลื่อนไหวสต็อก |
| `bronze_coupons` | `marketing_coupon` | ข้อมูลคูปอง |
| `bronze_loyalty_accounts` | `marketing_loyaltyaccount` | บัญชีสะสมแต้ม |
| `bronze_shipments` | `logistics_shipment` | ข้อมูลการจัดส่ง |

**ทุกตาราง Bronze มีฟิลด์เพิ่มเติม:**
- `_extract_ts` — เวลาที่ extract ข้อมูล
- `_source` — แหล่งที่มาของข้อมูล

---

## 🥈 Silver Layer (ข้อมูลที่ทำความสะอาดแล้ว)

ข้อมูลที่ผ่านการ deduplicate, normalize, และตรวจสอบคุณภาพ

### silver_products
| Column | Type | Description |
|---|---|---|
| `product_id` | UInt64 | PK - รหัสสินค้า |
| `sku` | String | SKU สินค้า (trimmed) |
| `product_name` | String | ชื่อสินค้า |
| `price` | Decimal(10,2) | ราคาขาย |
| `cost` | Decimal(10,2) | ราคาต้นทุน |
| `profit_margin` | Decimal(10,4) | อัตรากำไร = (price-cost)/price |

### silver_orders
| Column | Type | Description |
|---|---|---|
| `order_id` | UInt64 | PK - รหัสคำสั่งซื้อ |
| `customer_name` | String | ชื่อลูกค้า |
| `email` | String | อีเมล (lowercased) |
| `order_status` | String | สถานะ: pending/paid/shipped/cancelled |
| `payment_method` | String | วิธีชำระเงิน: credit/promptpay/cod |
| `order_date_key` | UInt32 | YYYYMMDD สำหรับ join dim_date |

### silver_loyalty_accounts
| Column | Type | Description |
|---|---|---|
| `loyalty_id` | UInt64 | PK |
| `points` | Int32 | แต้มสะสม |
| `tier` | String | ระดับสมาชิก (derived): Bronze/Silver/Gold/Platinum |

---

## 🥇 Gold Layer — Dimension Tables

### dim_date (ปฏิทิน)
| Column | Type | Description |
|---|---|---|
| `date_key` | UInt32 | PK - YYYYMMDD |
| `full_date` | Date | วันที่เต็ม |
| `year` | UInt16 | ปี ค.ศ. |
| `quarter` | UInt8 | ไตรมาส (1-4) |
| `month` | UInt8 | เดือน (1-12) |
| `month_name_th` | String | ชื่อเดือน (ภาษาไทย) |
| `day_name_th` | String | ชื่อวัน (ภาษาไทย) |
| `is_weekend` | UInt8 | วันหยุดสุดสัปดาห์ (0/1) |
| `fiscal_year` | UInt16 | ปีงบประมาณ (พ.ศ.) |

### dim_product (สินค้า)
| Column | Type | Description |
|---|---|---|
| `product_key` | UInt64 | PK - surrogate key |
| `sku` | String | รหัสสินค้า |
| `product_name` | String | ชื่อสินค้า |
| `current_price` | Decimal(10,2) | ราคาขายปัจจุบัน |
| `current_cost` | Decimal(10,2) | ต้นทุนปัจจุบัน |
| `profit_margin` | Decimal(10,4) | อัตรากำไร |

### dim_customer (ลูกค้า)
| Column | Type | Description |
|---|---|---|
| `customer_key` | UInt64 | PK - surrogate key |
| `customer_name` | String | ชื่อลูกค้า |
| `email` | String | อีเมล |
| `loyalty_tier` | String | ระดับสมาชิก |
| `total_orders` | UInt32 | จำนวนคำสั่งซื้อทั้งหมด |
| `total_spent` | Decimal(12,2) | ยอดซื้อรวมตลอดชีพ |

### dim_carrier (ผู้ให้บริการขนส่ง)
| Column | Type | Description |
|---|---|---|
| `carrier_key` | UInt64 | PK |
| `carrier_name` | String | ชื่อผู้ให้บริการ |

### dim_payment (วิธีชำระเงิน)
| Column | Type | Description |
|---|---|---|
| `payment_key` | UInt64 | PK |
| `payment_method` | String | รหัสวิธีชำระ |
| `payment_label` | String | ชื่อแสดงผล (ภาษาไทย) |

---

## 🥇 Gold Layer — Fact Tables

### fact_sales (ยอดขาย)
**Grain:** 1 row = 1 รายการสินค้าในคำสั่งซื้อ

| Column | Type | Description |
|---|---|---|
| `sale_id` | UInt64 | PK |
| `date_key` | UInt32 | FK → dim_date |
| `order_id` | UInt64 | รหัสคำสั่งซื้อ |
| `product_key` | UInt64 | FK → dim_product |
| `customer_key` | UInt64 | FK → dim_customer |
| `payment_key` | UInt64 | FK → dim_payment |
| `quantity` | UInt32 | จำนวนสินค้า |
| `unit_price` | Decimal(10,2) | ราคาต่อชิ้น |
| `unit_cost` | Decimal(10,2) | ต้นทุนต่อชิ้น |
| `line_total` | Decimal(10,2) | ยอดรวมก่อนส่วนลด |
| `discount_amount` | Decimal(10,2) | ส่วนลดที่ได้รับ |
| `net_revenue` | Decimal(10,2) | ยอดรวมหลังส่วนลด |
| `gross_profit` | Decimal(10,2) | กำไรขั้นต้น |

### fact_inventory (การเคลื่อนไหวสต็อก)
**Grain:** 1 row = 1 รายการเคลื่อนไหวสินค้า

| Column | Type | Description |
|---|---|---|
| `log_id` | UInt64 | PK |
| `date_key` | UInt32 | FK → dim_date |
| `product_key` | UInt64 | FK → dim_product |
| `log_type` | String | ประเภท: inbound/outbound/adjustment |
| `change_quantity` | Int32 | จำนวนที่เปลี่ยนแปลง (+/-) |

### fact_stock_snapshot (สแนปช็อตสต็อกรายวัน)
**Grain:** 1 row = 1 สินค้า ต่อ 1 วัน

| Column | Type | Description |
|---|---|---|
| `snapshot_date_key` | UInt32 | FK → dim_date |
| `product_key` | UInt64 | FK → dim_product |
| `current_quantity` | Int32 | จำนวนคงเหลือ |
| `is_low_stock` | UInt8 | สินค้าเหลือน้อย (0/1) |
| `days_of_supply` | Float32 | จำนวนวันที่คาดว่าจะหมด |

### fact_logistics (การจัดส่ง)
**Grain:** 1 row = 1 การจัดส่ง

| Column | Type | Description |
|---|---|---|
| `shipment_id` | UInt64 | PK |
| `date_key` | UInt32 | FK → dim_date |
| `carrier_key` | UInt64 | FK → dim_carrier |
| `shipment_status` | String | สถานะ: preparing/shipping/delivered/returned |
| `shipping_cost` | Decimal(10,2) | ค่าจัดส่ง |

### fact_marketing (คูปอง/โปรโมชั่น)
**Grain:** 1 row = 1 คูปอง

| Column | Type | Description |
|---|---|---|
| `coupon_id` | UInt64 | PK |
| `start_date_key` | UInt32 | FK → dim_date (เริ่มต้น) |
| `end_date_key` | UInt32 | FK → dim_date (สิ้นสุด) |
| `discount_type` | String | ประเภท: percentage/fixed |
| `discount_value` | Decimal(10,2) | มูลค่าส่วนลด |
| `times_used` | UInt32 | จำนวนครั้งที่ใช้ |
