DEBUG = True
TEMPLATE_DEBUG = True
SITE_ID = 1
INSTALLED_APPS = [
    'flooding_base',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_extensions',
    'markdown_deux',
    'south',
    'django_nose',  # Must be below south
    ]

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db'},
    }

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

ROOT_URLCONF = 'flooding_base.urls'
# Used for django-staticfiles
STATIC_URL = '/static_media/'
TEMPLATE_CONTEXT_PROCESSORS = (
    # Default items.
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    # Needs to be added for django-staticfiles to allow you to use
    # {{ STATIC_URL }}myapp/my.css in your templates.
    'django.contrib.staticfiles.context_processors.static_url',
    )

SECRET_KEY = 'x2s7u_s9b@wd0*ebtz1qiqzsavoh-f9ft1%bsti2*u-c3e180^'

try:
    # Import local settings that aren't stored in svn.
    from flooding_base.local_testsettings import *
except ImportError:
    pass
