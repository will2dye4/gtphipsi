# Django settings for gtphipsi.
# TODO: Set the global variable telling Django this is where this project's settings are.

DEBUG = True        # Change me!
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('William Dye', 'webmaster@gtphipsi.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'gtphipsi',
#        'USER': 'gtphipsi',
#        'PASSWORD': 'tester',
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/Users/William/dev/sqlite/gtphipsi',
        'HOST': '127.0.0.1',
        'PORT': '',                      # Set to empty string for default.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# The root directory for the project's source code.
GTPHIPSI_APP_ROOT = '/Users/William/dev/git/gtphipsi'  # Change me!

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = GTPHIPSI_APP_ROOT + '/media/' # Change me!

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = GTPHIPSI_APP_ROOT + '/media/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    GTPHIPSI_APP_ROOT + '/static',
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o^tpyccx8x3cjv&v!m^#uo)=8c_ejv041nca473%zylp%^af%&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
#   'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'gtphipsi.context_processors.announcements_processor',
    'gtphipsi.context_processors.menu_item_processor'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'gtphipsi.urls'

TEMPLATE_DIRS = (
    GTPHIPSI_APP_ROOT + '/templates',
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'brothers',
    'rush',
    'chapter',
)

TIME_LOGGING_FORMAT = '%d/%b/%Y %H:%M:%S'

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(module)s (%(asctime)s, %(process)d, %(thread)d) : %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s - %(levelname)s] %(message)s',
            'datefmt': TIME_LOGGING_FORMAT
        },
        'default': {
            'format': '[%(levelname)s] %(asctime)s %(module)s.%(funcName)s (%(lineno)d) : %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'app_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': GTPHIPSI_APP_ROOT + '/log/application.log'
        },
        'request_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': GTPHIPSI_APP_ROOT + '/log/request.log'
        },
        'query_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': GTPHIPSI_APP_ROOT + '/log/query.log'
        },
        'error_log': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': GTPHIPSI_APP_ROOT + '/log/error.log'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['app_log', 'error_log', 'console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['request_log', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.db.backends': {
            'handlers': ['query_log'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

AUTH_PROFILE_MODULE = 'brothers.UserProfile'

LOGIN_URL = '/login/'

FORBIDDEN_URL = '/forbidden/'

# Invoke test SMTP server with 'python -m smtpd -n -c DebuggingServer localhost:1025'
EMAIL_HOST = 'smtp.gmail.com'   # localhost

EMAIL_HOST_USER = 'webmaster@gtphipsi.org'

EMAIL_HOST_PASSWORD = 'gt1852'

EMAIL_PORT = 587    # 1025

EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


### gtphipsi-specific settings ###
URI_PREFIX = 'http://127.0.0.1:8000'    # Change me!

MAX_LOGIN_ATTEMPTS = 3

MIN_PASSWORD_LENGTH = 6

# Accepted formats:
# '1852-[0]2-19', '[0]2-19-1852', '[0]2-19-52', '[0]2/19/1852', '[0]2/19/52',
# 'Feb 19 1852', 'Feb 19, 1852', 'Feb 19 52', 'Feb 19, 52',
# '19 Feb 1852', '19 Feb, 1852', '19 Feb 52', '19 Feb, 52',
# 'February 19 1852', 'February 19, 1852', 'February 19 52', 'February 19, 52',
# '19 February 1852', '19 February, 1852', '19 February 52', '19 February, 52'
DATE_INPUT_FORMATS = [
    '%Y-%m-%d', '%m-%d-%Y', '%m-%d-%y', '%m/%d/%Y', '%m/%d/%y',
    '%b %d %Y', '%b %d, %Y', '%b %d %y', '%b %d, %y',
    '%d %b %Y', '%d %b, %Y', '%d %b %y', '%d %b, %y',
    '%B %d %Y', '%B %d, %Y', '%B %d %y', '%B %d, %y',
    '%d %B %Y', '%d %B, %Y', '%d %B %y', '%d %B, %y'
]

# Accepted formats:
# '14:30:59', '14:30',
# '2:30 PM', '2 PM'
TIME_INPUT_FORMATS = [
    '%H:%M:%S', '%H:%M',
    '%I:%M %p', '%I %p'
]

# Used to prevent just anyone from creating an account.
BROTHER_KEY = 'ba9fd881a99be6b644a43e73f52471f614a8c6115388b27836316672'

# Password to give to administrator users.
ADMIN_KEY = '21ad61523fbd563a8fe87860b16c4730f7d58cb08e4394af81c7c81f'

# Permissions to grant all undergraduate users when their accounts are created.
UNDERGRADUATE_PERMISSIONS = [
    'add_rush', 'change_rush', 'delete_rush',
    'add_rushevent', 'change_rushevent', 'delete_rushevent',
    'add_announcement', 'change_announcement', 'delete_announcement'
]

# Permissions to grant administrator users.
ADMINISTRATOR_PERMISSIONS = UNDERGRADUATE_PERMISSIONS + [
    'add_permission', #'change_permission', 'delete_permission',
    'add_group', 'change_group', 'delete_group',
    'add_user', 'change_user', 'delete_user',
    'add_userprofile', 'change_userprofile', 'delete_userprofile'
]