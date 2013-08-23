from djangoappengine.settings_base import *
from djangoappengine.utils import on_production_server

import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Settings for Django 1.4
DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {
                        'ENGINE': 'dbindexer',
                        'TARGET': 'native',
                        'HIGH_REPLICATION':True
                        }

# settings for Django 1.5
#DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': DATABASES['default']}
#DATABASES['default']['HIGH_REPLICATION']=True

if False:
    DATABASES['native'] = {
        'ENGINE': 'djangoappengine.db',

        'HIGH_REPLICATION': True,

        'DEV_APPSERVER_OPTIONS': {
            'high_replication' : True,
            'use_sqlite': True,
            }
    }


AUTOLOAD_SITECONF = 'dbindexes'
DBINDEXER_BACKENDS = (
    'dbindexer.backends.BaseResolver',
    'dbindexer.backends.FKNullFix',
    'dbindexer.backends.InMemoryJOINResolver',
)

# People who get code error notifications.
ADMINS = ( ('Alex Ashley', 'webmaster@digital-video.org.uk'))

SITE_ID = 1
APP_VERSION = 4.3

if on_production_server==True:
    from production_server import SECRET_KEY 
else:
    SECRET_KEY = '=r-$b*8hglm+858&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'
    DEBUG = True
    DATABASES['native']['DEV_APPSERVER_OPTIONS']= {      
                                                  'use_sqlite': True,
                                                  'high_replication': True,
                                                  #'port_sqlite_data':True
                                                  }
    
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = False
# First day of week, to be used on calendars
# 0 means Sunday, 1 means Monday...
FIRST_DAY_OF_WEEK = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to True, Django will format dates, numbers and calendars
# according to user current locale.
USE_L10N = False

INSTALLED_APPS = (
                  'django.contrib.contenttypes',
                  'django.contrib.staticfiles',
                  'django.contrib.auth',
                  'django.contrib.sessions',
                  'django.contrib.admin',
                  'djangotoolbox',
                  'util',
                  'project',
                  'ballot',
                  'timeline',
                  'system',
                  'report',
                  'djangoappengine',
                  'autoload',
                  'dbindexer',
                  )

TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
TEMPLATE_DIRS = (
                 os.path.join(os.path.dirname(__file__), 'templates'),
                 )

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

STATICFILES_URL = '/static/'
STATIC_URL = STATICFILES_URL
STATICFILES_DIRS = [MEDIA_ROOT]
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

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
