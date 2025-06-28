from pathlib import Path

import os
from google.cloud import firestore
import dotenv
from corsheaders.defaults import default_headers

dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Firestore Settings
# FIRESTORE_CLIENT = firestore.Client()
FIRESTORE_PROJECT_ID = os.environ.get('FIRESTORE_PROJECT_ID', 'gen-lang-client-0000121060')
FIRESTORE_DATABASE_ID = os.environ.get('FIRESTORE_DATABASE_ID', '(default)')
FIRESTORE_CREDENTIALS = os.getenv("FIRESTORE_CREDENTIALS", "./gen-lang-client-0000121060-ea7b2bef1534.json")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = FIRESTORE_CREDENTIALS    

# Firestore 클라이언트 생성
# FIRESTORE_CLIENT = firestore.Client()

# Google Cloud Settings
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')


print(os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]))  # True가 떠야 정상
print(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])  # 실제 경로 출력
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-bf8co_v&&)gz9&qove3w#dz44fil$-p+^60$t1f4onaeg=0da1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS', 'localhost')
CLIENT_ADDRESS = os.environ.get('CLIENT_ADDRESS', 'http://192.168.0.12:3000')

ALLOWED_HOSTS = [SERVER_ADDRESS, '127.0.0.1', 'localhost']

CORS_ALLOWED_ORIGINS = [CLIENT_ADDRESS]

CSRF_TRUSTED_ORIGINS = [CLIENT_ADDRESS]

CORS_ALLOW_CREDENTIALS = True  # 쿠키나 인증 토큰 포함 시
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
    'content-type',
]
# 임시: 모든 출처 허용 (POST preflight 테스트용)
CORS_ALLOW_ALL_ORIGINS = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'corsheaders',
    'rest_framework',
    'api',
    'firestore',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'uscheck_firestore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'uscheck_firestore.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
