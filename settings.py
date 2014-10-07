"""Settings for the gtphipsi web application."""

DEBUG = True
TEMPLATE_DEBUG = DEBUG

if DEBUG:
    # The root directory of the project's source code.
    GTPHIPSI_APP_ROOT = '/Users/William/Git/gtphipsi'
    # The domain name for the project.
    URI_PREFIX = 'http://127.0.0.1:8000'
    # Absolute filesystem path to the directory that will hold user-uploaded files.
    MEDIA_ROOT = GTPHIPSI_APP_ROOT + '/media/'
    # URL that handles the media served from MEDIA_ROOT. Make sure to use a trailing slash.
    MEDIA_URL = '/media/'
    # Absolute path to the directory static files should be collected to (not where they are stored in the project).
    STATIC_ROOT = GTPHIPSI_APP_ROOT + '/media/static/'
    # URL prefix for static files.
    STATIC_URL = '/static/'
    # Database configuration for the project.
    DATABASES = {
        'default': {
#           'ENGINE': 'django.db.backends.mysql',
#           'NAME': 'gtphipsi',
#           'USER': 'gtphipsi',
#           'PASSWORD': 'tester',
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/Users/William/Git/gtphipsi/gtphipsidb',
            'HOST': '127.0.0.1',
            'PORT': '',                      # Set to empty string for default.
        }
    }
else:
    GTPHIPSI_APP_ROOT = ''  # TODO fix
    URI_PREFIX = '' # TODO fix
    MEDIA_ROOT = '' # TODO fix
    MEDIA_URL = ''  # TODO fix
    STATIC_ROOT = ''    # TODO fix
    STATIC_URL = '' # TODO fix
    DATABASES = {}  # TODO FIX


# A tuple of tuples containing names and email addresses of people to email about server errors (HTTP status code 500).
ADMINS = (
    ('William Dye', 'webmaster@gtphipsi.org'),
)

AUTH_PROFILE_MODULE = 'brothers.UserProfile'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_HOST_USER = 'noreply@gtphipsi.org'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

EMAIL_HOST_PASSWORD = 'secret'

EMAIL_PORT = 587

EMAIL_SUBJECT_PREFIX = '[gtphipsi] '

EMAIL_USE_TLS = True

FORBIDDEN_URL = '/forbidden/'

IGNORABLE_404_STARTS = (
    '/iphone/',
    '/mobile/',
    '/mobi/',
    '/m/',
    '/apple',
    '/img/',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'gtphipsi.brothers',
    'gtphipsi.chapter',
    'gtphipsi.forums',
    'gtphipsi.officers',
    'gtphipsi.rest.v1',
    'gtphipsi.rush',
)

LANGUAGE_CODE = 'en-us'

# See http://docs.djangoproject.com/en/dev/topics/logging for more details on how to customize your logging configuration.
TIME_LOGGING_FORMAT = '%d/%b/%Y %H:%M:%S'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s (%(pathname)s, in %(funcName)s, line %(lineno)d, PID %(process)d) : %(message)s'
        },
        'default': {
            'format': '[%(levelname)s] %(asctime)s (%(filename)s, in %(funcName)s, line %(lineno)d) : %(message)s'
        },
        'query': {
            'format': '[%(asctime)s] %(message)s'
        }
    },
    'handlers': {
        'app_log': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'default',
            'filename': GTPHIPSI_APP_ROOT + '/log/application.log',
            'when': 'D',
            'interval': 7,
            'backupCount': 12,
        },
        'request_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'query',
            'filename': GTPHIPSI_APP_ROOT + '/log/request.log',
            'when': 'midnight',
            'backupCount': 100,
        },
        'query_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'query',
            'filename': GTPHIPSI_APP_ROOT + '/log/query.log',
            'when': 'midnight',
            'backupCount': 60,
        },
        'error_log': {
            'level': 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': GTPHIPSI_APP_ROOT + '/log/error.log',
            'when': 'midnight',
            'backupCount': 180,
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['app_log', 'error_log'],
            'level': 'INFO',
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

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

LOGOUT_URL = '/logout/'

# A tuple of tuples containing names and email addresses of people to email about broken links (HTTP status code 404).
MANAGERS = ADMINS

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

PHONE_NUMBER_FORMAT = r'\d{3}-\d{3}-\d{4}'

ROOT_URLCONF = 'gtphipsi.urls'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'o^tpyccx8x3cjv&v!m^#uo)=8c_ejv041nca473%zylp%^af%&'

SEND_BROKEN_LINK_EMAILS = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SITE_ID = 1

# Additional locations of static files. Don't forget to use absolute paths, not relative paths.
STATICFILES_DIRS = (
    GTPHIPSI_APP_ROOT + '/static',
)

# List of finder classes that know how to find static files in various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TIME_ZONE = 'America/New_York'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
#    'django.core.context_processors.debug',
#    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'gtphipsi.context_processors.announcements_processor',
    'gtphipsi.context_processors.user_profile_processor',
    'gtphipsi.context_processors.group_perms_processor',
    'gtphipsi.context_processors.menu_item_processor'
)

# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (
    GTPHIPSI_APP_ROOT + '/templates',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

USE_I18N = False

USE_L10N = True





## ============================================= ##
##                                               ##
##           gtphipsi-specific settings          ##
##                                               ##
## ============================================= ##


# Password to give to administrator users.
ADMIN_KEY = '21ad61523fbd563a8fe87860b16c4730f7d58cb08e4394af81c7c81f'

# Used to prevent just anyone from creating an account.
BROTHER_KEY = 'ba9fd881a99be6b644a43e73f52471f614a8c6115388b27836316672'

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

# Format: '1852-[0]2-19'
API_DATE_INPUT_FORMAT = '%Y-%m-%d'

# Format: '14:30:59'
API_TIME_INPUT_FORMAT = '%H:%M:%S'

# Format: '1852-[0]2-19T14:30:59'
API_DATE_TIME_INPUT_FORMAT = API_DATE_INPUT_FORMAT + 'T' + API_TIME_INPUT_FORMAT

# Django REST Framework settings.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

MAX_LOGIN_ATTEMPTS = 3

MIN_PASSWORD_LENGTH = 6

PASSWORD_RESET_CHARS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789%#@&_?'

ANNOUNCEMENTS_PER_PAGE = 20

POSTS_PER_PAGE = 15

# Permissions to grant to all alumni.
ALUMNI_PERMISSIONS = [
    'add_thread', 'change_thread', 'delete_thread',
    'add_post', 'change_post', 'delete_post'
]

# Permissions to grant all undergraduate users when their accounts are created.
UNDERGRADUATE_PERMISSIONS = ALUMNI_PERMISSIONS + [
    'add_rush', 'change_rush',
    'add_rushevent', 'change_rushevent',
    'add_announcement',
    'add_potential', 'change_potential', 'delete_potential'
]

# Permissions to grant administrator users.
ADMINISTRATOR_PERMISSIONS = UNDERGRADUATE_PERMISSIONS + [
    'delete_rush', 'delete_rushevent',
    'change_announcement', 'delete_announcement',
    'add_permission', 'change_permission', 'delete_permission',
    'add_group', 'change_group', 'delete_group',
    'add_user', 'change_user', 'delete_user',
    'add_userprofile', 'change_userprofile', 'delete_userprofile',
    'add_chapterofficer', 'change_chapterofficer', 'delete_chapterofficer',
    'add_officerhistory', 'change_officerhistory', 'delete_officerhistory',
    'add_forum', 'change_forum', 'delete_forum'
]
