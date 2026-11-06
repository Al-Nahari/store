"""
النماذج (Forms)
===============
تتحقق من مدخلات المستخدم (التحقق من الصحة Validation) قبل أي معالجة.
لا نثق أبداً بما يرسله المتصفح.
"""
import os

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Order, ProductOption

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


class OptionChoiceField(forms.ModelChoiceField):
    """حقل اختيار يعرض اسم الخيار مع سعره الإضافي."""

    def label_from_instance(self, obj):
        if obj.extra_price > 0:
            return f'{obj.name} (+{obj.extra_price})'
        return obj.name


class CustomizationForm(forms.Form):
    """
    نموذج تخصيص المنتج. يُبنى ديناميكياً حسب المنتج:
      - يظهر حقل «اللون» فقط إذا كان للمنتج خيارات ألوان.
      - يظهر حقل النص فقط إذا سمح المنتج بالنص ... وهكذا.
    """
    quantity = forms.IntegerField(
        label='الكمية', min_value=1, max_value=settings.MAX_QUANTITY_PER_ITEM, initial=1)
    custom_text = forms.CharField(
        label='النص المخصص', required=False, max_length=settings.MAX_CUSTOM_TEXT_LENGTH)
    uploaded_image = forms.ImageField(label='صورة أو شعار', required=False)

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

        # 1) حقول الخيارات (لون، مقاس) تُضاف فقط إن وُجدت للمنتج
        self.option_types = []
        for opt_type in ProductOption.OptionType.values:
            queryset = product.options.filter(option_type=opt_type)
            if queryset.exists():
                self.fields[opt_type] = OptionChoiceField(
                    queryset=queryset, empty_label=None, required=True,
                    label=ProductOption.OptionType(opt_type).label)
                self.option_types.append(opt_type)

        # 2) إزالة حقول التخصيص غير المسموحة لهذا المنتج
        if not product.allow_custom_text:
            del self.fields['custom_text']
        if not product.allow_custom_image:
            del self.fields['uploaded_image']

    def clean_uploaded_image(self):
        """قواعد أمان رفع الصور: النوع + الحجم."""
        image = self.cleaned_data.get('uploaded_image')
        if not image:
            return image

        extension = os.path.splitext(image.name)[1].lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise forms.ValidationError('الأنواع المسموحة: JPG, PNG, WEBP فقط.')

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if image.size > max_bytes:
            raise forms.ValidationError(
                f'حجم الصورة يجب ألا يتجاوز {settings.MAX_UPLOAD_SIZE_MB} ميجابايت.')
        return image

    def clean_custom_text(self):
        # إزالة المسافات الزائدة من البداية والنهاية
        return self.cleaned_data.get('custom_text', '').strip()


class CheckoutForm(forms.ModelForm):
    """نموذج بيانات التوصيل عند إتمام الطلب."""

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'address', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة تنسيق Bootstrap لكل الحقول
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RegisterForm(UserCreationForm):
    """نموذج إنشاء حساب جديد."""

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
