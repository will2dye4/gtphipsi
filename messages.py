# Message support for the gtphipsi application.

GTPHIPSI_MESSAGES = {
    'visibility.fullname':      '"Full name" refers to your middle name and/or nickname. Your first and last name are always visible.',
    'visibility.edit.public':   'Remember that your public profile is visible to anyone.',
    'visibility.edit.chapter':  'Your chapter profile is visible only to brothers with accounts. '
                                 'Consequently, you cannot hide your full name, big brother, major, hometown, or email address from this profile.',

    'email.infocard.subject':   'Your information card has been received',
    'email.infocard.body':      'Dear %s,\n\nYou submitted an information card on %s. Here is a copy of the '
                                 'information you submitted for your records:\n\n%s\n\nIf you have any questions, '
                                 'feel free to email me at webmaster@gtphipsi.org or our Membership Chair at '
                                 'membership@gtphipsi.org. We are very glad that you are interested in Phi Kappa Psi.'
                                 '\n\nYours,\ngtphipsi.org Webmaster',
    'email.contact.subject':    'Your message has been received',
    'email.contact.body':       'Dear %s,\n\nYou submitted a contact form on %s. Here is a copy of the '
                                 'information you submitted for your records:\n\n%s\n\nWe appreciate your interest '
                                 'in Phi Kappa Psi. Feel free to contact me at webmaster@gtphipsi.org if you have '
                                 'any questions.\n\nYours,\ngtphipsi.org Webmaster',
    'email.change.subject':     'Please confirm your email address',
    'email.change.body':        'Dear %s,\n\nYou recently requested to change the email address associated with '
                                 'your account. Please click the link below to confirm your new email address:\n\n'
                                 '%s/brothers/email/?hash=%s\n\nYours,\ngtphipsi.org Webmaster',

    'notify.announcement.subject':  'New announcement posted at gtphipsi.org',
    'notify.announcement.body':     'The following announcement was just posted by %s:\n\n%s%s\n\n'
                                     'Go to %s/chapter/announcements/ to see a list '
                                     'of all announcements.\n\nYours,\ngtphipsi.org Webmaster',
    'notify.infocard.subject':      'New information card submitted at gtphipsi.org',
    'notify.infocard.body':         'The following information card was submitted on %s:\n\n%s\n\n'
                                     'Go to %s/rush/infocards/ to see a list '
                                     'of all information cards.\n\nYours,\ngtphipsi.org Webmaster',
    'notify.contact.subject':      'New contact record submitted at gtphipsi.org',
    'notify.contact.body':         'The following contact record was submitted on %s:\n\n%s\n\nYours,\n'
                                    'gtphipsi.org Webmaster',
}

def get_message(key, default='', args=None):
    if key is None or not key or not GTPHIPSI_MESSAGES.has_key(key):
        message = default
    else:
        message = GTPHIPSI_MESSAGES.get(key)
        if args is not None:
            message = message % args
    return message
