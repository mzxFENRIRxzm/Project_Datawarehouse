import random
import string
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from sale.models import Product, Order, OrderItem
from logistics.models import Shipment

CUSTOMER_NAMES = [
    "สมชาย ใจดี", "วิภา รักเรียน", "ชัยวัฒน์ มั่นคง", "รัตนา เศรษฐี",
    "ประวิทย์ กล้าหาญ", "กาญจนา สดใส", "ธนากร รุ่งเรือง", "นภาพร แสนดี",
    "ศักดิ์ชัย พละกำลัง", "จินตนา อรุณรัศมี", "อภิชัย ธรรมรักษ์", "บุษบา แก้ววิเศษ",
    "พิชิต ทรัพย์ทวี", "สุภาวดี พรหมมา", "วรวุฒิ สุขสบาย", "ปราณี ตั้งใจ",
    "สมเกียรติ วัฒนา", "มัลลิกา จิตสว่าง", "ประสิทธิ์ มากมี", "ดาวเรือง พันธ์ดี",
    "ก้องเกียรติ นาคนิยม", "สายฝน ภักดี", "อำนาจ เจริญผล", "รุ่งทิพย์ สุขสันต์",
    "ณรงค์ กลิ่นหอม", "สาวิตรี ทองดี", "บัณฑิต อาภรณ์", "อุมาพร ศรีบุญ",
    "ทศพล มิ่งขวัญ", "พรรณี คงทรัพย์", "อดิศร พิทักษ์", "วาสนา อิ่มใจ",
    "ธีรภัทร ภิรมย์", "สุธิดา มากมั่ง", "ชาญชัย แก้วกาญจน์", "นันทนา เก่งกาจ",
    "ไกรสร พิริยะ", "พิมพา สมบัติ", "วรพจน์ สุขเกษม", "ศิริพร เจริญยิ่ง",
    "อนันต์ สุภาพ", "เพ็ญศรี น้ำใจ", "สามารถ ครุฑทอง", "อารี ประกอบผล",
    "ภานุวัฒน์ พ่วงดี", "นฤมล เรืองยศ", "กิตติชัย มณฑา", "สุชาดา สีลาพร",
    "สันติภาพ อยู่เย็น", "วนิดา ทรัพย์อนันต์",
]

STREETS = [
    "สุขุมวิท", "พหลโยธิน", "รัชดาภิเษก", "พระราม 9", "ลาดพร้าว",
    "เพชรบุรี", "เจริญกรุง", "สีลม", "สาทร", "บางนา-ตราด",
    "วิภาวดีรังสิต", "รามคำแหง", "ศรีนครินทร์", "พญาไท", "ราชวิถี",
    "ประดิษฐ์มนูธรรม", "นวมินทร์", "รังสิต-นครนายก", "กาญจนาภิเษก", "แจ้งวัฒนะ",
]

DISTRICTS = [
    "จตุจักร", "บางรัก", "ปทุมวัน", "คลองเตย", "ห้วยขวาง",
    "ลาดพร้าว", "ดินแดง", "บางกะปิ", "พระโขนง", "สวนหลวง",
    "บางเขน", "ดอนเมือง", "สายไหม", "หลักสี่", "ทุ่งครุ",
    "บางขุนเทียน", "บางบอน", "ภาษีเจริญ", "หนองแขม", "คลองสามวา",
]

CITIES = ["กรุงเทพมหานคร", "นนทบุรี", "สมุทรปราการ", "ปทุมธานี", "ชลบุรี", "พระนครศรีอยุธยา"]

CARRIERS = ["Kerry Express", "Flash Express", "EMS Thailand", "J&T Express", "DHL Express", "Ninja Van"]


def random_phone():
    prefixes = ["08", "09", "06"]
    return random.choice(prefixes) + "".join(random.choices(string.digits, k=8))


def random_email(name):
    name_part = name.replace(" ", "").lower()
    domains = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "suphasan.co.th"]
    return f"{name_part}{random.randint(1, 999)}@{random.choice(domains)}"


def random_address():
    house = random.randint(1, 999)
    village = random.choice(["", f" หมู่ {random.randint(1, 8)}", ""])
    street = random.choice(STREETS)
    district = random.choice(DISTRICTS)
    city = random.choice(CITIES)
    return f"{house}{village} ถนน{street} แขวง/เขต{district} จ.{city} {random.randint(10000, 10999)}"


class Command(BaseCommand):
    help = "Generate large-scale sale records with orders and shipments"

    def add_arguments(self, parser):
        parser.add_argument("--total", type=int, default=5000000, help="Total number of orders to create")
        parser.add_argument("--batch-size", type=int, default=1000, help="Orders per batch")
        parser.add_argument("--completed-ratio", type=float, default=0.8, help="Ratio of completed (paid) orders")

    def handle(self, *args, **options):
        total = options["total"]
        batch_size = options["batch_size"]
        completed_ratio = options["completed_ratio"]

        self.stdout.write(self.style.WARNING(
            f"Starting generation of {total:,} orders ({batch_size:,} per batch)..."
        ))
        self.stdout.write(self.style.WARNING(
            "This will also create ~3x OrderItems and ~80% Shipments. "
            "On SQLite this may take a VERY long time (potentially hours)."
        ))

        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR("No products found. Run `seed_data` first."))
            return

        self.stdout.write(f"Using {len(products)} products for order generation.")

        status_weights = [completed_ratio, 0.08, 0.07, 0.05]
        statuses = ["paid", "shipped", "pending", "cancelled"]

        created_orders = 0
        batch_count = 0
        start_time = timezone.now()

        while created_orders < total:
            batch_target = min(batch_size, total - created_orders)

            orders_batch = []
            batch_meta = []

            for _ in range(batch_target):
                customer_name = random.choice(CUSTOMER_NAMES)
                items_data = self._generate_order_items(products)
                total_price = sum(item["subtotal"] for item in items_data)
                discount = self._calculate_discount(total_price)
                status = random.choices(statuses, weights=status_weights, k=1)[0]

                orders_batch.append(Order(
                    customer_name=customer_name,
                    email=random_email(customer_name),
                    phone=random_phone(),
                    address=random_address(),
                    total_price=total_price,
                    discount_applied=discount,
                    final_price=total_price - discount,
                    status=status,
                    payment_method=random.choices(
                        ["promptpay", "credit", "cod"],
                        weights=[0.5, 0.3, 0.2],
                        k=1,
                    )[0],
                ))

                batch_meta.append({
                    "items_data": items_data,
                    "needs_shipment": status in ("paid", "shipped"),
                    "status": status,
                })

            with transaction.atomic():
                max_id_before = Order.objects.latest("id").id if Order.objects.exists() else 0

                Order.objects.bulk_create(orders_batch)

                created = list(Order.objects.filter(id__gt=max_id_before).order_by("id"))

                order_items = []
                shipments = []
                for i, order in enumerate(created):
                    meta = batch_meta[i]
                    for item_data in meta["items_data"]:
                        order_items.append(OrderItem(
                            order=order,
                            product=item_data["product"],
                            price=item_data["price"],
                            quantity=item_data["quantity"],
                        ))

                    if meta["needs_shipment"]:
                        shipments.append(Shipment(
                            order=order,
                            tracking_number=self._random_tracking(),
                            carrier=random.choice(CARRIERS),
                            shipping_cost=Decimal(str(random.choice([0, 50, 80, 100, 150, 200]))),
                            status="delivered" if meta["status"] == "paid" else "shipping",
                        ))

                OrderItem.objects.bulk_create(order_items)
                if shipments:
                    Shipment.objects.bulk_create(shipments)

            created_orders += len(created)
            batch_count += 1

            if batch_count % 10 == 0:
                elapsed = (timezone.now() - start_time).total_seconds()
                rate = created_orders / elapsed if elapsed > 0 else 0
                remaining = total - created_orders
                eta_seconds = remaining / rate if rate > 0 else 0
                self.stdout.write(
                    f"  Created {created_orders:,}/{total:,} orders "
                    f"({created_orders / total * 100:.1f}%) "
                    f"[{rate:.0f} orders/sec, ~{eta_seconds / 60:.0f} min remaining]"
                )

        total_elapsed = (timezone.now() - start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created_orders:,} orders, "
            f"{OrderItem.objects.count():,} order items, "
            f"in {total_elapsed / 60:.1f} minutes"
        ))

    def _generate_order_items(self, products):
        n_items = random.choices([1, 2, 3, 4, 5], weights=[0.2, 0.35, 0.25, 0.15, 0.05], k=1)[0]
        selected = random.sample(products, min(n_items, len(products)))
        items = []
        for product in selected:
            qty = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1], k=1)[0]
            items.append({
                "product": product,
                "price": product.price,
                "quantity": qty,
                "subtotal": product.price * qty,
            })
        return items

    def _calculate_discount(self, total_price):
        if total_price < Decimal("1000"):
            return Decimal("0.00")
        chance = random.random()
        if chance < 0.4:
            return Decimal("0.00")
        elif chance < 0.7:
            return (total_price * Decimal("0.05")).quantize(Decimal("0.01"))
        elif chance < 0.9:
            return (total_price * Decimal("0.10")).quantize(Decimal("0.01"))
        else:
            return (total_price * Decimal("0.15")).quantize(Decimal("0.01"))

    def _random_tracking(self):
        return "TH" + "".join(random.choices(string.ascii_uppercase + string.digits, k=14))
