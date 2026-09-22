from django.urls import path
from . import views

app_name = 'sale'

urlpatterns = [
    path('', views.index, name='index'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('checkout/', views.checkout, name='checkout'),
]
