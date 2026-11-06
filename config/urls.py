"""
الروابط الرئيسية للمشروع.
كل طلب يصل أولاً إلى هنا ثم يُوزَّع على التطبيق المناسب.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),                       # لوحة التحكم
    path('accounts/', include('django.contrib.auth.urls')),  # دخول/خروج جاهزة
    path('', include('store.urls')),                       # روابط المتجر
]

# في وضع التطوير فقط: عرض الصور المرفوعة من مجلد media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
