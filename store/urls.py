"""روابط تطبيق المتجر."""
from django.urls import path

from . import views

app_name = 'store'  # مساحة أسماء: نستخدم {% url 'store:home' %} في القوالب

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart'),
    path('cart/update/<str:key>/', views.cart_update, name='cart_update'),
    path('cart/remove/<str:key>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:pk>/success/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('register/', views.register, name='register'),
]
