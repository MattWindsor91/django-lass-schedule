USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

INSTALLED_APPS = (
    'lass_utils',
    'people',
    'metadata',
    'uryplayer',
    'schedule',
)
