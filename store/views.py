"""
العروض (Views) - قلب المنطق البرمجي
===================================
كل View دالة تستقبل طلب المتصفح (request) وترجع صفحة (response).

الصفحات:
  home            : عرض المنتجات (مع بحث وتصفية بالتصنيف)
  product_detail  : تفاصيل المنتج + نموذج التخصيص + الإضافة للسلة
  cart_detail     : عرض السلة
  cart_update     : تعديل كمية عنصر
  cart_remove     : حذف عنصر
  checkout        : إتمام الطلب وحفظه في قاعدة البيانات
  order_success   : صفحة نجاح الطلب
  my_orders       : طلباتي السابقة
  register        : إنشاء حساب
"""
import os
import uuid

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.conf import settings

from .cart import Cart
from .forms import CheckoutForm, CustomizationForm, RegisterForm
from .models import Category, Order, OrderItem, Product, ProductOption
from .pricing import build_options_summary


# ---------------------------------------------------------------------------
# 1) الصفحة الرئيسية: عرض المنتجات
# ---------------------------------------------------------------------------
def home(request):
    products = Product.objects.filter(is_active=True).select_related('category')

    # تصفية بالتصنيف: /?category=2
    category_id = request.GET.get('category', '')
    if category_id.isdigit():
        products = products.filter(category_id=category_id)

    # بحث بالاسم: /?q=كوب
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': int(category_id) if category_id.isdigit() else None,
        'query': query,
    }
    return render(request, 'store/home.html', context)


# ---------------------------------------------------------------------------
# 2) صفحة تفاصيل المنتج + التخصيص + الإضافة للسلة
# ---------------------------------------------------------------------------
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    if request.method == 'POST':
        # request.POST للنصوص، request.FILES للملفات (الصورة)
        form = CustomizationForm(request.POST, request.FILES, product=product)
        if form.is_valid():
            data = form.cleaned_data

            # الخيارات المختارة (لون/مقاس) كقائمة كائنات
            selected_options = [data[opt_type] for opt_type in form.option_types]

            # حفظ الصورة المرفوعة مؤقتاً بالقرص باسم عشوائي آمن.
            # (لا نستخدم اسم الملف الأصلي لتفادي الأسماء الخطرة أو المتكررة)
            image_path = ''
            image = data.get('uploaded_image')
            if image:
                extension = os.path.splitext(image.name)[1].lower()
                image_path = default_storage.save(
                    f'custom_uploads/{uuid.uuid4().hex}{extension}', image)

            cart = Cart(request)
            cart.add(
                product=product,
                options=selected_options,
                custom_text=data.get('custom_text', ''),
                image_path=image_path,
                quantity=data['quantity'],
            )
            messages.success(request, 'تمت إضافة المنتج المخصص إلى السلة.')
            return redirect('store:cart')
    else:
        form = CustomizationForm(product=product)

    # تجهيز مجموعات الخيارات للقالب (لون، مقاس) مع حقل النموذج المقابل
    option_groups = [
        {
            'type': opt_type,
            'label': ProductOption.OptionType(opt_type).label,
            'options': product.options.filter(option_type=opt_type),
            'field': form[opt_type],
        }
        for opt_type in form.option_types
    ]

    return render(request, 'store/product_detail.html', {
        'product': product,
        'form': form,
        'option_groups': option_groups,
    })


# ---------------------------------------------------------------------------
# 3) السلة
# ---------------------------------------------------------------------------
def cart_detail(request):
    cart = Cart(request)
    items = list(cart)  # نحوّلها لقائمة لأن الحساب يتم داخل __iter__
    total = sum((item['line_total'] for item in items), 0)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@require_POST
def cart_update(request, key):
    """تعديل كمية عنصر في السلة مع التحقق من الحدود."""
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    quantity = max(1, min(quantity, settings.MAX_QUANTITY_PER_ITEM))
    Cart(request).update_quantity(key, quantity)
    return redirect('store:cart')


@require_POST
def cart_remove(request, key):
    Cart(request).remove(key)
    messages.info(request, 'تم حذف العنصر من السلة.')
    return redirect('store:cart')


# ---------------------------------------------------------------------------
# 4) إتمام الطلب (يتطلب تسجيل الدخول)
# ---------------------------------------------------------------------------
@login_required
def checkout(request):
    cart = Cart(request)
    items = list(cart)
    if not items:
        messages.warning(request, 'السلة فارغة.')
        return redirect('store:cart')

    total = sum((item['line_total'] for item in items), 0)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # transaction.atomic: إما أن يُحفظ الطلب كاملاً أو لا يُحفظ شيء
            # (يمنع بقاء طلب ناقص إذا حدث خطأ في منتصف العملية)
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()

                for item in items:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        product_name=item['product'].name,   # نسخة وقت الشراء
                        options_summary=build_options_summary(item['options']),
                        custom_text=item['custom_text'],
                        uploaded_image=item['image_path'],   # مسار الملف المحفوظ
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],       # السعر النهائي المحسوب
                    )
                    order_item.options.set(item['options'])

                order.recalculate_total()

            cart.clear()
            messages.success(request, 'تم استلام طلبك بنجاح.')
            return redirect('store:order_success', pk=order.pk)
    else:
        # تعبئة اسم المستلم تلقائياً من بيانات الحساب
        form = CheckoutForm(initial={'full_name': request.user.get_full_name()})

    return render(request, 'store/checkout.html', {
        'form': form, 'items': items, 'total': total})


@login_required
def order_success(request, pk):
    # نشترط أن يكون الطلب للمستخدم الحالي حتى لا يرى أحد طلب غيره
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'store/my_orders.html', {'orders': orders})


# ---------------------------------------------------------------------------
# 5) إنشاء حساب
# ---------------------------------------------------------------------------
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # تسجيل الدخول مباشرة بعد إنشاء الحساب
            messages.success(request, 'تم إنشاء حسابك بنجاح.')
            return redirect('store:home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
