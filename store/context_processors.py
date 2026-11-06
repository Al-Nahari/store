"""
Context Processor: دالة تضيف متغيرات لكل القوالب تلقائياً
(بدل تمريرها يدوياً من كل View).
"""
from django.conf import settings

from .cart import Cart


def store_globals(request):
    return {
        'cart_count': len(Cart(request)),
        'CURRENCY': settings.CURRENCY,
    }
