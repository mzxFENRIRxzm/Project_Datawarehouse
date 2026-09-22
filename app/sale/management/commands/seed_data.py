from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from sale.models import Product, Order, OrderItem, Cart, CartItem
from inventory.models import StockLevel, StockLog
from marketing.models import Coupon, LoyaltyAccount
from logistics.models import Shipment
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds initial data for Suphasan platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing database data...')
        
        # Clear data
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        OrderItem.objects.all().delete()
        Shipment.objects.all().delete()
        Order.objects.all().delete()
        StockLog.objects.all().delete()
        StockLevel.objects.all().delete()
        Product.objects.all().delete()
        Coupon.objects.all().delete()
        LoyaltyAccount.objects.all().delete()
        
        self.stdout.write('Seeding new data...')
        
        try:
            with transaction.atomic():
                # 1. Create Products
                p1 = Product.objects.create(
                    name='MacBook Pro 16-inch M3 Max (36GB/1TB)',
                    sku='MBP-M3MAX-16',
                    description='แล็ปท็อประดับโปรที่แรงที่สุดด้วยชิป M3 Max หน้าจอ Liquid Retina XDR 16 นิ้ว เหมาะสำหรับงานตัดต่อวิดีโอ การเขียนโค้ดซอฟต์แวร์ระดับสูง และงานกราฟิก 3D',
                    price=95900.00,
                    cost=78000.00
                )
                p2 = Product.objects.create(
                    name='Keychron Q1 Max QMK Custom Mechanical Keyboard',
                    sku='KC-Q1MAX-B1',
                    description='คีย์บอร์ดกลไกไร้สายขนาด 75% โครงสร้างอลูมิเนียม Full-CNC เชื่อมต่อผ่าน 2.4GHz / Bluetooth 5.1 / Type-C คีย์แคป PBT Double-shot โปรไฟล์ KSA',
                    price=6900.00,
                    cost=4500.00
                )
                p3 = Product.objects.create(
                    name='Logitech MX Master 3S Wireless Mouse',
                    sku='LOGI-MX3S-GR',
                    description='เมาส์ไร้สายเพื่อการทำงานระดับมืออาชีพ เทคโนโลยีเซ็นเซอร์ Darkfield 8,000 DPI ปุ่มคลิกที่เงียบลง 90% และล้อเลื่อนเหล็กกล้าแบบ MagSpeed Electromagnetic',
                    price=4200.00,
                    cost=2800.00
                )
                p4 = Product.objects.create(
                    name='Dell UltraSharp 32-inch 4K USB-C Monitor (U3223QE)',
                    sku='DELL-U3223QE',
                    description='จอภาพระดับพรีเมียมขนาด 31.5 นิ้ว ความละเอียด 4K UHD เทคโนโลยี IPS Black ให้คอนทราสต์ที่สูงกว่า IPS ทั่วไปถึง 2 เท่า พร้อม USB-C Hub กำลังไฟ 90W',
                    price=34900.00,
                    cost=26000.00
                )
                
                self.stdout.write('Products seeded successfully.')
                
                # 2. Create Stock Levels
                StockLevel.objects.create(product=p1, quantity=12, location='Rack-A3', reorder_point=3)
                StockLevel.objects.create(product=p2, quantity=25, location='Rack-B2', reorder_point=5)
                StockLevel.objects.create(product=p3, quantity=40, location='Rack-B5', reorder_point=8)
                StockLevel.objects.create(product=p4, quantity=8, location='Rack-A1', reorder_point=2)
                
                # 3. Create Stock Logs
                for p, qty in [(p1, 12), (p2, 25), (p3, 40), (p4, 8)]:
                    StockLog.objects.create(
                        product=p,
                        change_quantity=qty,
                        log_type='inbound',
                        reason='นำสินค้าเข้าระบบครั้งแรก (จัดซื้อนำเข้า)'
                    )
                
                self.stdout.write('Inventory stocks seeded successfully.')
                
                # 4. Create Coupons
                now = timezone.now()
                Coupon.objects.create(
                    code='WELCOME10',
                    discount_type='percentage',
                    value=10.00,
                    min_purchase=1000.00,
                    start_date=now - timedelta(days=2),
                    end_date=now + timedelta(days=60),
                    active=True
                )
                Coupon.objects.create(
                    code='SUPHASAN500',
                    discount_type='fixed',
                    value=500.00,
                    min_purchase=5000.00,
                    start_date=now - timedelta(days=2),
                    end_date=now + timedelta(days=30),
                    active=True
                )
                Coupon.objects.create(
                    code='SUPERDEAL',
                    discount_type='percentage',
                    value=20.00,
                    min_purchase=15000.00,
                    start_date=now - timedelta(days=2),
                    end_date=now + timedelta(days=15),
                    active=True
                )
                
                self.stdout.write('Promo coupons seeded successfully.')
                
                # 5. Create Loyalty Accounts
                LoyaltyAccount.objects.create(
                    customer_name='สมคิด รักดี',
                    phone='0897654321',
                    points=450
                )
                LoyaltyAccount.objects.create(
                    customer_name='จารุวรรณ ตั้งใจ',
                    phone='0812345678',
                    points=1250
                )
                
                self.stdout.write('Loyalty accounts seeded successfully.')
                
            self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding database: {str(e)}'))
