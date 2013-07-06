try:
    from djangoappengine.settings_base import *
    has_djangoappengine = True
except ImportError:
    has_djangoappengine = False
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

import os

SITE_ID = 1
APP_VERSION = 3.3
SECRET_KEY = ''

INSTALLED_APPS = (
                  'autoload',
                  'djangotoolbox',
                  'django.contrib.auth',
                  'django.contrib.admin',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  #'dbindexer',
                  'timeline',
                  'util',
                  'project',
                  'ballot',
                  'report',
                  )

if has_djangoappengine:
    INSTALLED_APPS = ('djangoappengine',) + INSTALLED_APPS

TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

STATICFILES_ROOT = MEDIA_ROOT 
STATICFILES_URL = '/media/'

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
