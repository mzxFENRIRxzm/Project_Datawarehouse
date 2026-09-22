from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Product, Cart, CartItem, Order, OrderItem
from inventory.models import StockLevel, StockLog
from marketing.models import Coupon, LoyaltyAccount
from logistics.models import Shipment
import random

def get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
    return cart

def index(request):
    products = Product.objects.all()
    cart = get_or_create_cart(request)
    
    # Check if a coupon is currently applied in session
    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount = 0
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
        except Coupon.DoesNotExist:
            request.session['coupon_code'] = None

    # Calculate cart prices
    subtotal = cart.total_price()
    
    if coupon:
        if subtotal >= coupon.min_purchase:
            if coupon.discount_type == 'percentage':
                discount = (subtotal * coupon.value) / 100
            else:
                discount = coupon.value
            # discount cannot exceed subtotal
            discount = min(discount, subtotal)
        else:
            messages.warning(request, f"คูปอง {coupon.code} ต้องมียอดซื้อขั้นต่ำ {coupon.min_purchase} บาท")
            request.session['coupon_code'] = None
            
    final_price = subtotal - discount
    shipping_cost = 50 if subtotal > 0 else 0  # Flat rate shipping
    
    context = {
        'products': products,
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'final_price': final_price,
        'shipping_cost': shipping_cost,
        'total_with_shipping': final_price + shipping_cost,
        'coupon': coupon,
    }
    return render(request, 'sale/index.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check stock
    try:
        stock = StockLevel.objects.get(product=product)
        available = stock.quantity
    except StockLevel.DoesNotExist:
        available = 0
        
    if available <= 0:
        messages.error(request, f"ขออภัย สินค้า {product.name} หมดสต็อก")
        return redirect('sale:index')
        
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        if cart_item.quantity + 1 > available:
            messages.error(request, f"ขออภัย สินค้าในสต็อกไม่พอ (มีสินค้าพร้อมส่ง {available} ชิ้น)")
            return redirect('sale:index')
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.success(request, f"เพิ่ม {product.name} ลงตะกร้าแล้ว")
        
    return redirect('sale:index')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"ลบ {product_name} ออกจากตะกร้าแล้ว")
    return redirect('sale:index')

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        if not code:
            request.session['coupon_code'] = None
            messages.info(request, "ยกเลิกคูปองแล้ว")
            return redirect('sale:index')
            
        try:
            coupon = Coupon.objects.get(code=code, active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
            request.session['coupon_code'] = coupon.code
            messages.success(request, f"ใช้คูปอง {coupon.code} สำเร็จ!")
        except Coupon.DoesNotExist:
            messages.error(request, "ไม่พบคูปองนี้ หรือคูปองหมดอายุการใช้งาน")
            request.session['coupon_code'] = None
            
    return redirect('sale:index')

def checkout(request):
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        if not cart.items.exists():
            messages.error(request, "ไม่มีสินค้าในตะกร้า")
            return redirect('sale:index')
            
        customer_name = request.POST.get('customer_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        
        # Calculate pricing
        subtotal = cart.total_price()
        coupon_code = request.session.get('coupon_code')
        coupon = None
        discount = 0
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
                if subtotal >= coupon.min_purchase:
                    if coupon.discount_type == 'percentage':
                        discount = (subtotal * coupon.value) / 100
                    else:
                        discount = coupon.value
                    discount = min(discount, subtotal)
            except Coupon.DoesNotExist:
                pass
                
        final_price = subtotal - discount
        shipping_cost = 50  # Flat rate
        
        # Check and lock stock inside a transaction
        try:
            with transaction.atomic():
                # Verify stock first
                for item in cart.items.all():
                    stock = StockLevel.objects.select_for_update().get(product=item.product)
                    if stock.quantity < item.quantity:
                        raise ValueError(f"สินค้า {item.product.name} มีสต็อกไม่เพียงพอ (คงเหลือ {stock.quantity} ชิ้น)")
                
                # Create Order
                order = Order.objects.create(
                    customer_name=customer_name,
                    email=email,
                    phone=phone,
                    address=address,
                    total_price=subtotal,
                    discount_applied=discount,
                    final_price=final_price,
                    status='paid',  # Mock: Set as paid directly for easy demonstration
                    payment_method=payment_method
                )
                
                # Add OrderItems and deduct stock
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity
                    )
                    
                    # Deduct stock
                    stock = StockLevel.objects.get(product=item.product)
                    stock.quantity -= item.quantity
                    stock.save()
                    
                    # Create StockLog
                    StockLog.objects.create(
                        product=item.product,
                        change_quantity=-item.quantity,
                        log_type='outbound',
                        reason=f"ขายผ่านคำสั่งซื้อ #{order.id}"
                    )
                
                # Create Loyalty Points (Marketing integration: 100 THB = 1 Point)
                points_earned = int(final_price // 100)
                if points_earned > 0:
                    loyalty_acc, created = LoyaltyAccount.objects.get_or_create(
                        phone=phone,
                        defaults={'customer_name': customer_name}
                    )
                    loyalty_acc.points += points_earned
                    loyalty_acc.save()
                    messages.success(request, f"คุณได้รับแต้มสะสมเพิ่ม {points_earned} แต้ม! (เบอร์: {phone})")

                # Create Shipment (Logistics integration)
                # Generate a mock tracking number (e.g. SP20260616-XXXX)
                rand_num = random.randint(1000, 9999)
                tracking = f"SP{timezone.now().strftime('%Y%m%d')}{rand_num}"
                
                Shipment.objects.create(
                    order=order,
                    tracking_number=tracking,
                    carrier='Flash Express',  # Default mock carrier
                    shipping_cost=shipping_cost,
                    status='preparing'
                )
                
                # Clear cart and coupon in session
                cart.items.all().delete()
                request.session['coupon_code'] = None
                
                messages.success(request, f"สั่งซื้อสินค้าและชำระเงินเรียบร้อยแล้ว! หมายเลขคำสั่งซื้อของคุณคือ #{order.id}")
                messages.info(request, f"เลขติดตามพัสดุของคุณคือ: {tracking} (จัดส่งโดย Flash Express)")
                return redirect('sale:index')
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('sale:index')
            
    return redirect('sale:index')
