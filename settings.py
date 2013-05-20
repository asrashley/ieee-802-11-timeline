try:
    from djangoappengine.settings_base import *
    has_djangoappengine = True
except ImportError:
    has_djangoappengine = False
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

import os

SECRET_KEY = '=r-$b*8hglm+858dslfkjdlsjs&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'

INSTALLED_APPS = (
    'djangotoolbox',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'dbindexer',
    'timeline',
    'util',
    'project',
    'ballot'
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

#TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
#                               "django.core.context_processors.debug",
#                               "django.core.context_processors.i18n",
#                               "django.contrib.staticfiles.context_processors.staticfiles",
#                               "django.contrib.messages.context_processors.messages",
#                               )

# Activate django-dbindexer if available
try:
    import dbindexer
    DATABASES['native'] = DATABASES['default']
    DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
    INSTALLED_APPS += ('dbindexer',)
except ImportError:
    #print 'Warning, unable to import dbindexer'
    pass
