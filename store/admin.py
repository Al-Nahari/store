"""
لوحة التحكم (Admin)
===================
تعرض كل الجداول، مع تركيز على إظهار تفاصيل التخصيص (النص والصورة)
للمدير داخل صفحة الطلب نفسها ليتمكن من التنفيذ بدقة.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Order, OrderItem, Product, ProductOption


def image_html(image_field, height=70):
    """دالة مساعدة: ترجع وسم <img> قابل للنقر لعرض الصورة بالحجم الكامل."""
    if image_field:
        return format_html(
            '<a href="{0}" target="_blank"><img src="{0}" style="max-height:{1}px;'
            'border-radius:6px;border:1px solid #ccc"></a>', image_field.url, height)
    return '—'


# ------------------------------ التصنيفات -----------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# ------------------------------ المنتجات + الخيارات --------------------------
class ProductOptionInline(admin.TabularInline):
    """يسمح بإضافة خيارات المنتج (ألوان/مقاسات) من نفس صفحة المنتج."""
    model = ProductOption
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'base_price',
                    'allow_custom_text', 'allow_custom_image', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)
    inlines = [ProductOptionInline]

    @admin.display(description='الصورة')
    def thumbnail(self, obj):
        return image_html(obj.image, 40)


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('product', 'option_type', 'name', 'extra_price')
    list_filter = ('option_type', 'product')
    search_fields = ('name', 'product__name')


# ------------------------------ الطلبات -------------------------------------
class OrderItemInline(admin.TabularInline):
    """
    عناصر الطلب داخل صفحة الطلب. كلها للقراءة فقط (لا يجوز تعديل ما اشتراه
    العميل)، وتُظهر النص المخصص والصورة المرفوعة بوضوح.
    """
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('product_name', 'options_summary', 'custom_text',
              'image_preview', 'quantity', 'unit_price', 'line_total_display')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='الصورة المرفوعة')
    def image_preview(self, obj):
        return image_html(obj.uploaded_image, 90)

    @admin.display(description='إجمالي العنصر')
    def line_total_display(self, obj):
        return obj.line_total


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'phone', 'status',
                    'total_price', 'has_customization', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)       # تغيير حالة الطلب من القائمة مباشرة
    search_fields = ('id', 'full_name', 'phone', 'user__username')
    readonly_fields = ('user', 'total_price', 'created_at')
    inlines = [OrderItemInline]
    actions = ['mark_confirmed', 'mark_in_production', 'mark_shipped']

    @admin.display(boolean=True, description='فيه تخصيص؟')
    def has_customization(self, obj):
        """✔ إذا كان أي عنصر في الطلب يحتوي نصاً أو صورة مخصصة."""
        return any(item.custom_text or item.uploaded_image for item in obj.items.all())

    @admin.action(description='تحويل الطلبات المحددة إلى: تم التأكيد')
    def mark_confirmed(self, request, queryset):
        queryset.update(status=Order.Status.CONFIRMED)

    @admin.action(description='تحويل الطلبات المحددة إلى: قيد التنفيذ')
    def mark_in_production(self, request, queryset):
        queryset.update(status=Order.Status.IN_PRODUCTION)

    @admin.action(description='تحويل الطلبات المحددة إلى: تم الشحن')
    def mark_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """عرض مستقل لكل عناصر التخصيص عبر كل الطلبات."""
    list_display = ('order', 'product_name', 'options_summary',
                    'custom_text', 'image_preview', 'quantity', 'unit_price')
    list_filter = ('order__status',)
    search_fields = ('product_name', 'custom_text', 'order__id')
    readonly_fields = ('image_preview',)

    @admin.display(description='الصورة المرفوعة')
    def image_preview(self, obj):
        return image_html(obj.uploaded_image, 60)
