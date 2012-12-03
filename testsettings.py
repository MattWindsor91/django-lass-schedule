USE_TZ = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'lass_utils',
    'people',
    'metadata',
    'uryplayer',
    'schedule',
)
