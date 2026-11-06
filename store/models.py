"""
نماذج قاعدة البيانات (Models)
=============================
كل Class هنا يتحول إلى جدول في قاعدة البيانات.

العلاقات:
    Category  1 ──< Product  1 ──< ProductOption
    User      1 ──< Order    1 ──< OrderItem >── Product
    OrderItem >──< ProductOption   (علاقة متعدد-إلى-متعدد: لون + مقاس)
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    """التصنيف: مثل (أكواب، ملابس، هدايا)."""
    name = models.CharField('اسم التصنيف', max_length=100, unique=True)
    description = models.TextField('الوصف', blank=True)

    class Meta:
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """المنتج الأساسي (قبل التخصيص)."""
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,  # PROTECT: يمنع حذف تصنيف فيه منتجات
        related_name='products', verbose_name='التصنيف')
    name = models.CharField('اسم المنتج', max_length=200)
    description = models.TextField('الوصف', blank=True)
    base_price = models.DecimalField(
        'السعر الأساسي', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))])
    image = models.ImageField('صورة المنتج', upload_to='products/', blank=True)

    # أي أنواع التخصيص يسمح بها هذا المنتج؟ (مثلاً الكوب يقبل نصاً وصورة)
    allow_custom_text = models.BooleanField('يسمح بنص مخصص', default=True)
    allow_custom_image = models.BooleanField('يسمح برفع صورة', default=True)

    is_active = models.BooleanField('معروض في المتجر', default=True)
    created_at = models.DateTimeField('تاريخ الإضافة', auto_now_add=True)

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    """
    خيار قابل للاختيار لمنتج معين (لون أو مقاس) مع سعر إضافي.
    مثال: المنتج «كوب» ← الخيار (لون: أسود، +500).
    """

    class OptionType(models.TextChoices):
        COLOR = 'color', 'اللون'
        SIZE = 'size', 'المقاس'

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,  # CASCADE: حذف المنتج يحذف خياراته
        related_name='options', verbose_name='المنتج')
    option_type = models.CharField('نوع الخيار', max_length=10, choices=OptionType.choices)
    name = models.CharField('اسم الخيار', max_length=100)
    color_code = models.CharField(
        'كود اللون', max_length=7, blank=True,
        help_text='اختياري للألوان فقط، مثال: #FF0000')
    extra_price = models.DecimalField(
        'السعر الإضافي', max_digits=10, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))])

    class Meta:
        verbose_name = 'خيار منتج'
        verbose_name_plural = 'خيارات المنتجات'
        ordering = ['option_type', 'name']
        # يمنع تكرار نفس الخيار لنفس المنتج
        unique_together = ('product', 'option_type', 'name')

    def __str__(self):
        return f'{self.product.name} - {self.get_option_type_display()}: {self.name}'


class Order(models.Model):
    """الطلب: يجمع عناصر السلة بعد إتمام الشراء."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد المراجعة'
        CONFIRMED = 'confirmed', 'تم التأكيد'
        IN_PRODUCTION = 'in_production', 'قيد التنفيذ'
        SHIPPED = 'shipped', 'تم الشحن'
        DELIVERED = 'delivered', 'تم التسليم'
        CANCELLED = 'cancelled', 'ملغي'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='orders', verbose_name='المستخدم')
    created_at = models.DateTimeField('تاريخ الطلب', auto_now_add=True)
    status = models.CharField(
        'الحالة', max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(
        'السعر الإجمالي', max_digits=12, decimal_places=2, default=Decimal('0'))

    # بيانات التوصيل
    full_name = models.CharField('اسم المستلم', max_length=150)
    phone = models.CharField('رقم الهاتف', max_length=20)
    address = models.TextField('العنوان')
    notes = models.TextField('ملاحظات', blank=True)

    class Meta:
        verbose_name = 'طلب'
        verbose_name_plural = 'الطلبات'
        ordering = ['-created_at']

    def __str__(self):
        return f'طلب رقم {self.pk} - {self.user}'

    def recalculate_total(self):
        """يعيد حساب الإجمالي من مجموع عناصر الطلب ثم يحفظه."""
        self.total_price = sum((item.line_total for item in self.items.all()), Decimal('0'))
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    """
    تفاصيل الطلب: كل صف = منتج واحد مخصص بمواصفات محددة.
    نحفظ السعر والاسم وقت الشراء (Snapshot) حتى لا يتأثر الطلب القديم
    إذا غيّر المدير أسعار المنتجات لاحقاً.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name='الطلب')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name='المنتج')
    product_name = models.CharField('اسم المنتج وقت الشراء', max_length=200)

    # الخيارات المختارة (لون ومقاس..) + نص مختصر لها يسهل عرضه للمدير
    options = models.ManyToManyField(
        ProductOption, blank=True, verbose_name='الخيارات المختارة')
    options_summary = models.CharField('ملخص الخيارات', max_length=255, blank=True)

    # بيانات التخصيص
    custom_text = models.CharField('النص المخصص', max_length=100, blank=True)
    uploaded_image = models.ImageField(
        'الصورة المرفوعة', upload_to='custom_uploads/', blank=True)

    quantity = models.PositiveIntegerField(
        'الكمية', default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        'السعر النهائي للوحدة', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'عنصر طلب'
        verbose_name_plural = 'عناصر الطلبات'

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

    @property
    def line_total(self):
        """إجمالي هذا العنصر = سعر الوحدة × الكمية."""
        return self.unit_price * self.quantity
