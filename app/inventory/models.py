from django.db import models
from sale.models import Product

class StockLevel(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock', verbose_name="สินค้า")
    quantity = models.IntegerField(default=0, verbose_name="จำนวนคงเหลือ")
    location = models.CharField(max_length=100, default='A-1', verbose_name="ตำแหน่งชั้นวาง")
    reorder_point = models.IntegerField(default=5, verbose_name="จุดแจ้งเตือนสินค้าเหลือน้อย")

    def __str__(self):
        return f"สต็อก {self.product.name}: {self.quantity} ชิ้น (ชั้น {self.location})"

    def is_low_stock(self):
        return self.quantity <= self.reorder_point

class StockLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('inbound', 'รับเข้าสินค้า'),
        ('outbound', 'นำสินค้าออก'),
        ('adjustment', 'ปรับปรุงยอดสต็อก'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="สินค้า")
    change_quantity = models.IntegerField(verbose_name="จำนวนที่เปลี่ยน")
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, verbose_name="ประเภทรายการ")
    reason = models.CharField(max_length=255, blank=True, verbose_name="เหตุผล/บันทึกเพิ่มเติม")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="เวลาทำรายการ")

    def __str__(self):
        return f"{self.get_log_type_display()} - {self.product.name} ({self.change_quantity:+} ชิ้น)"
