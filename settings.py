from djangoappengine.settings_base import *
from djangoappengine.utils import on_production_server

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}

#DATABASES = {
#    'native': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    },
#    'default': {
#                'ENGINE': 'dbindexer',
#                 'TARGET': 'native'
#                 },
#}
AUTOLOAD_SITECONF = 'indexes'

SITE_ID = 1
APP_VERSION = 3.3

if on_production_server==True:
    from production_server import SECRET_KEY 
else:
    SECRET_KEY = '=r-$b*8hglm+858&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'
    DEBUG = True
    
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = True
USE_TZ = False

INSTALLED_APPS = (
                  'django.contrib.contenttypes',
                  'django.contrib.auth',
                  'django.contrib.sessions',
                  'django.contrib.admin',
                  'djangotoolbox',
                  'autoload',
                  'dbindexer',
                  'timeline',
                  'util',
                  'project',
                  'ballot',
                  'report',
                  'djangoappengine',
                  )

TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

STATICFILES_ROOT = MEDIA_ROOT 
STATICFILES_URL = '/media/'
STATIC_URL = '/static/'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/' 

ROOT_URLCONF = 'urls'

MIDDLEWARE_CLASSES = ('autoload.middleware.AutoloadMiddleware',
                      'django.middleware.common.CommonMiddleware',
                      'django.contrib.sessions.middleware.SessionMiddleware',
                      'django.middleware.csrf.CsrfViewMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',
                      'django.contrib.messages.middleware.MessageMiddleware',)

TEMPLATE_CONTEXT_PROCESSORS = ("util.context_processors.site_context",
                               "django.contrib.auth.context_processors.auth",
                               "django.core.context_processors.debug",
                               "django.core.context_processors.request",
                               "django.core.context_processors.media",
                               "django.contrib.messages.context_processors.messages",
                               )
#                               "django.contrib.staticfiles.context_processors.staticfiles",
#                               "django.core.context_processors.i18n",

# Activate django-dbindexer if available
#try:
#    import dbindexer
#    DATABASES['native'] = DATABASES['default']
#    DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
#    INSTALLED_APPS += ('dbindexer',)
#except ImportError:
#    #print 'Warning, unable to import dbindexer'
#    pass
