from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU สินค้า")
    description = models.TextField(verbose_name="รายละเอียดสินค้า", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาขาย")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาต้นทุน")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="รูปภาพสินค้า")

    class Meta:
        db_table = 'storefront_product'

    def __str__(self):
        return f"{self.name} ({self.sku})"

class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'storefront_cart'

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'storefront_cartitem'

    def subtotal(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอชำระเงิน'),
        ('paid', 'ชำระเงินแล้ว'),
        ('shipped', 'จัดส่งแล้ว'),
        ('cancelled', 'ยกเลิก'),
    ]
    PAYMENT_CHOICES = [
        ('credit', 'บัตรเครดิต/เดบิต'),
        ('promptpay', 'QR PromptPay'),
        ('cod', 'เก็บเงินปลายทาง (COD)'),
    ]
    customer_name = models.CharField(max_length=100, verbose_name="ชื่อลูกค้า")
    email = models.EmailField(verbose_name="อีเมล")
    phone = models.CharField(max_length=20, verbose_name="เบอร์โทรศัพท์")
    address = models.TextField(verbose_name="ที่อยู่จัดส่ง")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคารวม")
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="ส่วนลด")
    final_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคาสุทธิ")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะออเดอร์")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='promptpay', verbose_name="วิธีการชำระเงิน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สั่งซื้อเมื่อ")

    class Meta:
        db_table = 'storefront_order'

    def __str__(self):
        return f"ออเดอร์ #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'storefront_orderitem'

    def subtotal(self):
        return self.price * self.quantity
