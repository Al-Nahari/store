"""
أمر لإدخال بيانات تجريبية: python manage.py seed_data
مفيد لتجربة المشروع فوراً وقت العرض أمام اللجنة.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Category, Product, ProductOption

# (النوع، الاسم، كود اللون، السعر الإضافي)
COLORS = [
    ('color', 'أبيض', '#FFFFFF', '0'),
    ('color', 'أسود', '#212529', '500'),
    ('color', 'أحمر', '#C0392B', '300'),
    ('color', 'أزرق', '#2E6BE6', '300'),
]
MUG_SIZES = [('size', 'صغير (250 مل)', '', '0'), ('size', 'كبير (400 مل)', '', '700')]
SHIRT_SIZES = [('size', 'M', '', '0'), ('size', 'L', '', '0'), ('size', 'XL', '', '400')]
PILLOW_SIZES = [('size', '40×40 سم', '', '0'), ('size', '50×50 سم', '', '600')]

PRODUCTS = [
    ('أكواب', 'كوب سيراميك مخصص', 'كوب عالي الجودة يُطبع عليه اسمك أو صورتك.',
     '2500', COLORS, MUG_SIZES, True, True),
    ('ملابس', 'تيشيرت مطبوع', 'تيشيرت قطني بطباعة حسب طلبك.',
     '6000', COLORS, SHIRT_SIZES, True, True),
    ('هدايا', 'وسادة هدية', 'وسادة ناعمة بتصميم شخصي.',
     '4000', COLORS[:3], PILLOW_SIZES, True, True),
    ('هدايا', 'درع تذكاري', 'درع بنص منقوش فقط (بدون صور).',
     '8000', [], [], True, False),
]


class Command(BaseCommand):
    help = 'إدخال تصنيفات ومنتجات تجريبية'

    def handle(self, *args, **options):
        for cat, name, desc, price, colors, sizes, txt, img in PRODUCTS:
            category, _ = Category.objects.get_or_create(name=cat)
            product, created = Product.objects.get_or_create(
                name=name, defaults={
                    'category': category, 'description': desc,
                    'base_price': Decimal(price),
                    'allow_custom_text': txt, 'allow_custom_image': img})
            if created:
                for opt_type, opt_name, code, extra in colors + sizes:
                    ProductOption.objects.create(
                        product=product, option_type=opt_type, name=opt_name,
                        color_code=code, extra_price=Decimal(extra))
        self.stdout.write(self.style.SUCCESS('تم إدخال البيانات التجريبية بنجاح.'))
