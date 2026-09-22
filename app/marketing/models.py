from django.db import models

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'เปอร์เซ็นต์ส่วนลด (%)'),
        ('fixed', 'จำนวนเงินส่วนลด (บาท)'),
    ]
    code = models.CharField(max_length=50, unique=True, verbose_name="รหัสคูปอง")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage', verbose_name="ประเภทส่วนลด")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="มูลค่าส่วนลด")
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="ยอดซื้อขั้นต่ำ")
    active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    start_date = models.DateTimeField(verbose_name="วันที่เริ่มต้น")
    end_date = models.DateTimeField(verbose_name="วันที่สิ้นสุด")

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()} ({self.value})"

class LoyaltyAccount(models.Model):
    customer_name = models.CharField(max_length=100, verbose_name="ชื่อลูกค้า")
    phone = models.CharField(max_length=20, unique=True, verbose_name="เบอร์โทรศัพท์")
    points = models.IntegerField(default=0, verbose_name="แต้มสะสม")

    def __str__(self):
        return f"{self.customer_name} ({self.phone}) - {self.points} แต้ม"
