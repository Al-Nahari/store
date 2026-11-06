"""
إعدادات المشروع (Settings)
=========================
هذا الملف يحدد: التطبيقات المثبتة، قاعدة البيانات، القوالب، الملفات الثابتة،
وملفات الوسائط (الصور المرفوعة)، واللغة العربية.
"""
import os
from pathlib import Path

# المسار الجذري للمشروع (المجلد الذي يحتوي manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# مفتاح الأمان: في الإنتاج يجب وضعه في متغير بيئة وعدم كتابته في الكود
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-insecure-key-change-me')

# وضع التطوير. يجب جعله False عند النشر الفعلي
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# ---------------------------------------------------------------------------
# التطبيقات المثبتة
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',         # لوحة التحكم الجاهزة
    'django.contrib.auth',          # المستخدمون وتسجيل الدخول
    'django.contrib.contenttypes',
    'django.contrib.sessions',      # الجلسات (نخزن فيها السلة)
    'django.contrib.messages',      # رسائل التنبيه للمستخدم
    'django.contrib.staticfiles',
    'store',                        # تطبيق المتجر الخاص بنا
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # حماية النماذج من هجمات CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # مجلد القوالب العام
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # يوفر عدد عناصر السلة والعملة لكل القوالب
                'store.context_processors.store_globals',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# قاعدة البيانات: SQLite (ملف db.sqlite3 يُنشأ تلقائياً)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# اللغة والوقت
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Aden'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# الملفات الثابتة (CSS) وملفات الوسائط (صور المنتجات وصور العملاء)
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# إعدادات تسجيل الدخول
# ---------------------------------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'store:home'
LOGOUT_REDIRECT_URL = 'store:home'

# ---------------------------------------------------------------------------
# إعدادات خاصة بالمتجر
# ---------------------------------------------------------------------------
CURRENCY = 'ريال'                       # رمز العملة المعروض
MAX_UPLOAD_SIZE_MB = 2                  # أقصى حجم لصورة التخصيص
MAX_CUSTOM_TEXT_LENGTH = 30             # أقصى طول للنص المخصص
MAX_QUANTITY_PER_ITEM = 20              # أقصى كمية للعنصر الواحد
