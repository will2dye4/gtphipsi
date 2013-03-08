"""Message support for the gtphipsi web application, providing a unified repository for long literal strings.

This module exports the following functions:
    - get_message (key[, default, args])

"""


GTPHIPSI_MESSAGES = {
    'login.account.invalid':    'You have entered an invalid username or password. '
                                 'Please check your credentials and try again.',
    'login.account.disabled':   'Your account has been disabled. Please contact an administrator to have it re-enabled.',
    'login.account.locked':     'You have attempted to sign in with the wrong credentials too many times. '
                                 'Please contact an administrator to have your account reset.',

    'visibility.fullname':      '"Full name" refers to your middle name and/or nickname. '
                                 'Your first and last name are always visible.',
    'visibility.edit.public':   'Remember that your public profile is visible to anyone.',
    'visibility.edit.chapter':  'Your chapter profile is visible only to brothers with accounts. '
                                 'Consequently, you cannot hide your full name, big brother, major, hometown, '
                                 'or email address from this profile.',

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
    'email.password.subject':     'Your password has been reset',
    'email.password.reset':       'Your password for gtphipsi.org has been reset successfully',
    'email.password.admin.reset': 'An administrator has just reset your password for gtphipsi.org',
    'email.password.body':          'Dear %s,\n\n%s. The next time you sign in, please use the following temporary password.'
                                     '\n\nPassword: %s\n\nAfter signing in, you will be prompted to change your password '
                                     'to something more memorable.\n\nCheers,\ngtphipsi Webmaster',
    'email.new_password.subject':   'Your password has changed',
    'email.new_password.body':      'Dear %s,\n\nYour password for gtphipsi.org has recently been changed.\n\n'
                                     'If you changed your password, you may disregard this email. However, if you '
                                     'did not change your password, please contact the webmaster at webmaster@gtphipsi.org '
                                     'and request to have your password reset immediately.\n\nYours,\ngtphipsi Webmaster',

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

    'profile.password.reset':   'Your password was recently reset. Please use the form below to change your password '
                                 'to something more memorable. You will need the temporary password you were emailed.',

    'group.name.invalid':       'The group name you entered is invalid. Please enter a different name.',
    'group.name.exists':        'A group with that name already exists. Please enter a different name.',
    'group.name.nonempty':      'You must enter a name for this group.',
    'group.perms.nonempty':     'You must select at least one permission for this group.',

    'officer.brother.invalid':  'Please select a brother from the list below.',
    'officer.office.invalid':   'Please select an office from the list below.',

    'time.format.invalid':      'Enter a valid time (e.g., 2 PM, 2:30 PM, 14:30, 14:30:59).',
}


def get_message(key, default='', args=None):
    """Return a formatted string corresponding to the provided key and arguments.

    Required parameters:
        - key   =>  the key (in GTPHIPSI_MESSAGES) of the message to return

    Optional parameters:
        - default   =>  the value to return if the key is not found in the dictionary of messages: defaults to ''
        - args      =>  a tuple of arguments to use for formatting the message: defaults to none

    """
    if key is None or not key or not GTPHIPSI_MESSAGES.has_key(key):
        message = default
    else:
        message = GTPHIPSI_MESSAGES.get(key)
        if args is not None:
            message = message % args
    return message
