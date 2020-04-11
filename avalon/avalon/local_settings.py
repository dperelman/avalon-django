from settings import *

ALLOWED_HOSTS = [ u'avalon.aweirdimagination.net' ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'avalon',
        'USER': 'avalon',
        'ATOMIC_REQUESTS': True,
    }
}

STATIC_URL = '/static/'
