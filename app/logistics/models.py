from django.db import models
from sale.models import Order

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('preparing', 'กำลังเตรียมสินค้า'),
        ('shipping', 'อยู่ระหว่างจัดส่ง'),
        ('delivered', 'จัดส่งสำเร็จ'),
        ('returned', 'ส่งคืนสินค้า'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment', verbose_name="ออเดอร์")
    tracking_number = models.CharField(max_length=50, blank=True, verbose_name="เลขติดตามพัสดุ (Tracking Number)")
    carrier = models.CharField(max_length=50, verbose_name="ผู้ให้บริการขนส่ง")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าจัดส่ง")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing', verbose_name="สถานะขนส่ง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="อัปเดตล่าสุดเมื่อ")

    def __str__(self):
        return f"ขนส่งออเดอร์ #{self.order.id} ({self.carrier})"
