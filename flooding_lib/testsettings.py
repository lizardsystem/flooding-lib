import os

DEBUG = True
TEMPLATE_DEBUG = True
TMP_DIR = '/tmp/'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'flooding_lib',
        'USER': 'flooding',
        'PASSWORD': 'flooding',
        'HOST': 'db',
        'PORT': 5432, # Mapnik requires an explicit port number
        }
}

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

# BUILDOUT_DIR is for access to the "surrounding" buildout, for instance for
# BUILDOUT_DIR/var/media files to give django-staticfiles a proper place
# to place all collected static files.
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))

FLOODING_SHARE = os.path.join(BUILDOUT_DIR, 'var')

SITE_ID = 1
INSTALLED_APPS = [
    'flooding_lib',
    'flooding_lib.tools.importtool',
    'flooding_lib.tools.exporttool',
    'flooding_lib.tools.approvaltool',
    'flooding_lib.tools.pyramids',
    'flooding_lib.tools.gdmapstool',  # see if this fixes the tests
    'flooding_lib.sharedproject',
    'flooding_presentation',
    'flooding_visualization',
    'lizard_worker',
    'django_extensions',
    'django_nose',
    'flooding_base',
    'django.contrib.staticfiles',
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
    'django.contrib.staticfiles.context_processors.static_url',
    )

SECRET_KEY = '!*8^643&bd5ltic(laa6!mt&9$e7#!p)v7m^$0c%3%wx8zs-_-'

RASTER_SERVER_URL = 'http://dummy/'

try:
    from flooding_lib.localsettings import *
except ImportError:
    pass
