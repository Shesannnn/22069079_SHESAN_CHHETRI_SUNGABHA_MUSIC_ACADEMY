import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-_mo^*9332x(l$dj%xz0)uypgt*0ws16$^&xpvz1ox%wp(vgbkt'
DEBUG = True
ALLOWED_HOSTS = []

# Jazzmin configuration for admin panel
JAZZMIN_SETTINGS = {
    # Branding
    "site_title": "Sungabha Music Academy Admin",
    "site_header": "Sungabha Music Academy",
    "site_brand": "Sungabha Admin",
    "site_logo": "images/Logo.png",
    "site_logo_classes": None,
    "site_icon": "images/Logo.png",
    "welcome_sign": "Welcome to Sungabha Music Academy Admin",
    "copyright": "Sungabha Music Academy 2025",
    # Top Menu Links
    "topmenu_links": [
        {"name": "Home", "url": "home", "permissions": ["auth.view_user"]},
        {"name": "Courses", "url": "courses_list", "permissions": ["auth.view_user"]},
        {"name": "Contact", "url": "contact", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "sungabha.Course": "fas fa-music",
        "sungabha.Profile": "fas fa-id-card",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-arrow-circle-right",
    # UI Tweaks
    "custom_css": "css/sungabha-admin.css",  # Points to CSS with smaller logo (30px)
    "custom_js": None,
    "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # Search and Modals
    "search_model": ["auth.User", "sungabha.Course"],
    "related_modal_active": True,
}

APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'music',  # Note: Ensure this matches your app name (previously 'sungabha')
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sungabha.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sungabha.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Khalti Configuration (uses NPR for payments)
KHALTI_PUBLIC_KEY = "f967e2e517664ea8a37e7ac01601f6a3"  # Sandbox public key
KHALTI_SECRET_KEY = "e207d9449a7a4f3e87930a34a23a8732"  # Sandbox secret key
KHALTI_INITIATE_URL = "https://dev.khalti.com/api/v2/epayment/initiate/"  # Sandbox initiate URL
KHALTI_VERIFY_URL = "https://dev.khalti.com/api/v2/epayment/lookup/"  # Sandbox lookup endpoint
KHALTI_RETURN_URL = "http://localhost:8000/payment/success/"
WEBSITE_URL = "http://localhost:8000/"  # For local testing

# Session Settings for Local Testing
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False  # For http://localhost
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'payment.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'music.views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sungabhamusicacademy@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'xzjh ckzz htcy ogvg'  # Replace with the App Password
DEFAULT_FROM_EMAIL = 'sungabhamusicacademy@gmail.com'