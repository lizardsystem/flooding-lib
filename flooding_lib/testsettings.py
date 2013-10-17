DEBUG = True
TEMPLATE_DEBUG = True
TMP_DIR = '/tmp/'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'flooding_lib_test',
        'USER': 'buildout',
        'PASSWORD': 'buildout',
        'HOST': '',
        'PORT': ''
        }
}

SITE_ID = 1
INSTALLED_APPS = [
    'flooding_lib',
    'flooding_lib.tools.importtool',
    'flooding_lib.tools.exporttool',
    'flooding_lib.tools.approvaltool',
    'flooding_lib.tools.pyramids',
    'flooding_lib.sharedproject',
    'flooding_presentation',
    'flooding_visualization',
    'lizard_worker',
    'django_extensions',
    'django_nose',
    'flooding_base',
    'staticfiles',
    'django.contrib.gis',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    ]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

ROOT_URLCONF = 'flooding_lib.urls'

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
    'staticfiles.context_processors.static_url',
    )

try:
    from flooding_lib.localsettings import *
except ImportError:
    pass
