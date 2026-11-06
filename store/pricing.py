"""
منطق حساب الأسعار
=================
فصلنا الحساب في ملف مستقل ليكون:
  1) سهل الشرح أمام لجنة التقييم.
  2) سهل الاختبار.
  3) مستخدماً في مكان واحد فقط (لا تكرار للمعادلة).

المعادلة:
    السعر النهائي للوحدة = السعر الأساسي + مجموع الأسعار الإضافية للخيارات
    إجمالي العنصر        = السعر النهائي للوحدة × الكمية
"""
from decimal import Decimal


def calculate_unit_price(product, options):
    """
    product : كائن Product
    options : قائمة كائنات ProductOption المختارة
    """
    extras = sum((opt.extra_price for opt in options), Decimal('0'))
    return product.base_price + extras


def calculate_line_total(unit_price, quantity):
    """إجمالي عنصر السلة."""
    return unit_price * quantity


def build_options_summary(options):
    """نص مختصر للخيارات، مثال: «اللون: أسود، المقاس: كبير»."""
    return '، '.join(f'{opt.get_option_type_display()}: {opt.name}' for opt in options)
