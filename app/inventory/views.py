from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from sale.models import Product
from .models import StockLevel, StockLog

def dashboard(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_product':
            # Add a completely new product
            name = request.POST.get('name')
            sku = request.POST.get('sku').strip().upper()
            description = request.POST.get('description', '')
            price = request.POST.get('price')
            cost = request.POST.get('cost')
            initial_stock = int(request.POST.get('initial_stock', 0))
            location = request.POST.get('location', 'A-1')
            reorder_point = int(request.POST.get('reorder_point', 5))
            
            if Product.objects.filter(sku=sku).exists():
                messages.error(request, f"ไม่สามารถเพิ่มได้ เนื่องจากมี SKU '{sku}' อยู่แล้วในระบบ")
                return redirect('inventory:dashboard')
                
            try:
                with transaction.atomic():
                    # Create Product
                    product = Product.objects.create(
                        name=name,
                        sku=sku,
                        description=description,
                        price=price,
                        cost=cost
                    )
                    # Create StockLevel
                    StockLevel.objects.create(
                        product=product,
                        quantity=initial_stock,
                        location=location,
                        reorder_point=reorder_point
                    )
                    # Create StockLog
                    StockLog.objects.create(
                        product=product,
                        change_quantity=initial_stock,
                        log_type='inbound',
                        reason="จดทะเบียนและรับเข้าสต็อกสินค้าเริ่มแรก"
                    )
                messages.success(request, f"เพิ่มสินค้า '{name}' และสร้างสต็อกจำนวน {initial_stock} ชิ้น สำเร็จ!")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")
                
        elif action == 'add_stock':
            # Add stock to an existing product (Inbound)
            product_id = request.POST.get('product_id')
            quantity_to_add = int(request.POST.get('quantity', 0))
            reason = request.POST.get('reason', 'รับสินค้าเข้าเพิ่มเติม')
            
            product = get_object_or_404(Product, id=product_id)
            
            try:
                with transaction.atomic():
                    stock = StockLevel.objects.get(product=product)
                    stock.quantity += quantity_to_add
                    stock.save()
                    
                    StockLog.objects.create(
                        product=product,
                        change_quantity=quantity_to_add,
                        log_type='inbound',
                        reason=reason
                    )
                messages.success(request, f"เพิ่มสต็อก '{product.name}' จำนวน {quantity_to_add} ชิ้น สำเร็จ! (รวมคงเหลือ {stock.quantity} ชิ้น)")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")
                
        return redirect('inventory:dashboard')
        
    # GET request
    stock_levels = StockLevel.objects.all().select_related('product')
    stock_logs = StockLog.objects.all().select_related('product').order_by('-created_at')[:10]
    products = Product.objects.all()
    
    # Calculate some warehouse stats
    total_items = sum(stock.quantity for stock in stock_levels)
    low_stock_count = sum(1 for stock in stock_levels if stock.is_low_stock())
    sku_count = stock_levels.count()
    
    context = {
        'stock_levels': stock_levels,
        'stock_logs': stock_logs,
        'products': products,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'sku_count': sku_count,
    }
    return render(request, 'inventory/dashboard.html', context)
