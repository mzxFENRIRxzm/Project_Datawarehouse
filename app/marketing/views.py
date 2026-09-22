from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Coupon, LoyaltyAccount
from datetime import datetime, timedelta

def dashboard(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_coupon':
            code = request.POST.get('code').strip().upper()
            discount_type = request.POST.get('discount_type')
            value = request.POST.get('value')
            min_purchase = request.POST.get('min_purchase', 0.00)
            
            start_str = request.POST.get('start_date')
            end_str = request.POST.get('end_date')
            
            # Fallback dates if empty
            if start_str:
                start_date = timezone.make_aware(datetime.strptime(start_str, '%Y-%m-%dT%H:%M'))
            else:
                start_date = timezone.now()
                
            if end_str:
                end_date = timezone.make_aware(datetime.strptime(end_str, '%Y-%m-%dT%H:%M'))
            else:
                end_date = timezone.now() + timedelta(days=30)
                
            if Coupon.objects.filter(code=code).exists():
                messages.error(request, f"มีคูปองรหัส '{code}' อยู่ในระบบแล้ว")
                return redirect('marketing:dashboard')
                
            try:
                Coupon.objects.create(
                    code=code,
                    discount_type=discount_type,
                    value=value,
                    min_purchase=min_purchase,
                    start_date=start_date,
                    end_date=end_date,
                    active=True
                )
                messages.success(request, f"สร้างคูปอง '{code}' สำเร็จแล้ว!")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาดในการสร้างคูปอง: {str(e)}")
                
        elif action == 'create_member':
            customer_name = request.POST.get('customer_name')
            phone = request.POST.get('phone').strip()
            points = int(request.POST.get('points', 0))
            
            if LoyaltyAccount.objects.filter(phone=phone).exists():
                messages.error(request, f"มีหมายเลขสมาชิกเบอร์ '{phone}' ในระบบแล้ว")
                return redirect('marketing:dashboard')
                
            try:
                LoyaltyAccount.objects.create(
                    customer_name=customer_name,
                    phone=phone,
                    points=points
                )
                messages.success(request, f"ลงทะเบียนสมาชิก '{customer_name}' สำเร็จแล้ว!")
            except Exception as e:
                messages.error(request, f"เกิดข้อผิดพลาดในการสมัครสมาชิก: {str(e)}")
                
        return redirect('marketing:dashboard')
        
    # GET request
    coupons = Coupon.objects.all().order_by('-end_date')
    members = LoyaltyAccount.objects.all().order_by('-points')
    
    # Calculate stats
    active_coupons = Coupon.objects.filter(active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now()).count()
    total_members = members.count()
    total_points = sum(m.points for m in members)
    
    context = {
        'coupons': coupons,
        'members': members,
        'active_coupons': active_coupons,
        'total_members': total_members,
        'total_points': total_points,
    }
    return render(request, 'marketing/dashboard.html', context)
