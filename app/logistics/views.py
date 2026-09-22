from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Shipment
from sale.models import Order

def dashboard(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_shipment':
            shipment_id = request.POST.get('shipment_id')
            carrier = request.POST.get('carrier')
            tracking_number = request.POST.get('tracking_number').strip()
            status = request.POST.get('status')
            
            shipment = get_object_or_404(Shipment, id=shipment_id)
            
            try:
                shipment.carrier = carrier
                shipment.tracking_number = tracking_number
                shipment.status = status
                shipment.save()
                
                # Sync order status based on shipping status
                order = shipment.order
                if status == 'delivered':
                    order.status = 'shipped'
                order.save()
                
                messages.success(request, f"อัปเดตสถานะการขนส่งออเดอร์ #{order.id} เรียบร้อยแล้ว!")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")
                
        return redirect('logistics:dashboard')
        
    # GET request
    shipments = Shipment.objects.all().select_related('order').order_by('-updated_at')
    
    # Stats
    total_shipments = shipments.count()
    preparing_count = shipments.filter(status='preparing').count()
    shipping_count = shipments.filter(status='shipping').count()
    delivered_count = shipments.filter(status='delivered').count()
    
    context = {
        'shipments': shipments,
        'total_shipments': total_shipments,
        'preparing_count': preparing_count,
        'shipping_count': shipping_count,
        'delivered_count': delivered_count,
    }
    return render(request, 'logistics/dashboard.html', context)

def track(request):
    tracking_number = request.GET.get('q', '').strip()
    shipment = None
    searched = False
    
    if tracking_number:
        searched = True
        try:
            shipment = Shipment.objects.select_related('order').get(tracking_number__iexact=tracking_number)
        except Shipment.DoesNotExist:
            pass
            
    context = {
        'shipment': shipment,
        'searched': searched,
        'query': tracking_number,
    }
    return render(request, 'logistics/track.html', context)
