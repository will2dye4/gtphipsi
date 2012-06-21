# Message support for the gtphipsi application.

GTPHIPSI_MESSAGES = {
    'visibility.fullname': '"Full name" refers to your middle name and/or nickname. Your first and last name are always visible.',
    'visibility.edit.public': 'Remember that your public profile is visible to anyone.',
    'visibility.edit.chapter': 'Your chapter profile is visible only to brothers with accounts. \
                                Consequently, you cannot hide your full name, big brother, major, hometown, or email address from this profile.',
}

def get_message(key, default=''):
    if key is None or not key or not GTPHIPSI_MESSAGES.has_key(key):
        return default
    return GTPHIPSI_MESSAGES.get(key)
