"""
السلة (Cart) باستخدام الجلسات (Sessions)
=======================================
Django يعطي كل زائر «جلسة» (Session) مرتبطة بـ Cookie. نخزن فيها السلة
كقاموس (Dictionary) بهذا الشكل:

    session['cart'] = {
        'a1b2c3...': {                      # مفتاح فريد لكل عنصر مخصص
            'product_id': 3,
            'option_ids': [5, 9],
            'custom_text': 'أحمد',
            'image_path': 'custom_uploads/xxxx.png',
            'quantity': 2,
        },
    }

ملاحظة أمنية مهمة: لا نخزن الأسعار في الجلسة! نخزن المعرّفات فقط ونعيد
حساب السعر من قاعدة البيانات في كل مرة، حتى لا يستطيع أحد التلاعب بالسعر.
"""
import uuid

from django.core.files.storage import default_storage

from .models import Product, ProductOption
from .pricing import calculate_line_total, calculate_unit_price

SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        # نقرأ فقط ولا ننشئ جلسة جديدة إلا عند الإضافة الفعلية
        self.data = self.session.get(SESSION_KEY, {})

    # ------------------------------ عمليات التعديل ------------------------
    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True  # نخبر Django أن الجلسة تغيّرت

    def add(self, product, options, custom_text='', image_path='', quantity=1):
        """
        يضيف عنصراً مخصصاً. كل إضافة = سطر مستقل في السلة، لأن كوبين بنصين
        مختلفين هما منتجان مختلفان فعلياً.
        """
        key = uuid.uuid4().hex
        self.data[key] = {
            'product_id': product.pk,
            'option_ids': [opt.pk for opt in options],
            'custom_text': custom_text,
            'image_path': image_path,
            'quantity': quantity,
        }
        self._save()
        return key

    def update_quantity(self, key, quantity):
        if key in self.data:
            self.data[key]['quantity'] = quantity
            self._save()

    def remove(self, key):
        """يحذف عنصراً ويحذف صورته المرفوعة من القرص حتى لا تتراكم الملفات."""
        item = self.data.pop(key, None)
        if item:
            if item.get('image_path'):
                default_storage.delete(item['image_path'])
            self._save()

    def clear(self):
        """
        يفرّغ السلة بعد إتمام الطلب. لا نحذف الصور لأنها أصبحت مرتبطة
        بعناصر الطلب (OrderItem).
        """
        self.session.pop(SESSION_KEY, None)
        self.session.modified = True

    # ------------------------------ القراءة --------------------------------
    def __iter__(self):
        """
        يمرّ على عناصر السلة ويُرجع قاموساً غنياً لكل عنصر (المنتج، الخيارات،
        السعر المحسوب ...). هذا ما تستخدمه القوالب وعملية إتمام الطلب.
        """
        for key, raw in list(self.data.items()):
            try:
                product = Product.objects.get(pk=raw['product_id'], is_active=True)
            except Product.DoesNotExist:
                self.remove(key)  # المنتج حُذف أو أُخفي: نزيله من السلة
                continue

            options = list(
                ProductOption.objects.filter(pk__in=raw['option_ids'], product=product))
            unit_price = calculate_unit_price(product, options)
            quantity = raw['quantity']

            yield {
                'key': key,
                'product': product,
                'options': options,
                'custom_text': raw['custom_text'],
                'image_path': raw['image_path'],
                'image_url': default_storage.url(raw['image_path']) if raw['image_path'] else '',
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': calculate_line_total(unit_price, quantity),
            }

    def __len__(self):
        """عدد القطع الكلي (يظهر في شارة السلة بالقائمة العلوية)."""
        return sum(item['quantity'] for item in self.data.values())

    def get_total_price(self):
        return sum((item['line_total'] for item in self), 0)
