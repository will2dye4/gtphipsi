"""Models for the gtphipsi.officers package.

This module exports the following model classes:
    - ChapterOfficer
    - OfficerHistory

This module exports the following tuples of field choices:
    - OFFICER_CHOICES

"""

from django.db import models

from gtphipsi.brothers.models import UserProfile


# List of officer positions within the chapter.
OFFICER_CHOICES = (
    ('GP', 'President'),
    ('VGP', 'Vice President'),
    ('P', 'Treasurer'),
    ('AG', 'Corresponding Secretary'),
    ('BG', 'Recording Secretary'),
    ('SG', 'Historian'),
    ('Hod', 'Messenger'),
    ('Phu', 'Sergeant at Arms'),
    ('Hi', 'Chaplain'),
    ('IFC', 'IFC Representative'),
#    ('HM', 'House Manager')
)


class ChapterOfficer(models.Model):
    """A current officer of the chapter, associating an undergraduate brother with an officer position."""

    office = models.CharField(choices=OFFICER_CHOICES, max_length=3)
    brother = models.ForeignKey(UserProfile, related_name='offices')
    updated = models.DateField()


class OfficerHistory(models.Model):
    """A historical record of officer positions, tracking which brothers held which officer positions in the past."""

    office = models.CharField(choices=OFFICER_CHOICES, max_length=3)
    brother = models.ForeignKey(UserProfile, related_name='former_offices')
    start = models.DateField(verbose_name='Start date')
    end = models.DateField(verbose_name='End date')
