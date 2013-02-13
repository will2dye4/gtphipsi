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


# Represents a current officer of the chapter.
class ChapterOfficer(models.Model):
    office = models.CharField(choices=OFFICER_CHOICES, max_length=3)
    brother = models.ForeignKey(UserProfile)
    updated = models.DateTimeField(auto_now=True)


# Maintains a history of which brothers held which officer positions in the past.
class OfficerHistory(models.Model):
    office = models.CharField(choices=OFFICER_CHOICES, max_length=5)
    brother = models.ForeignKey(UserProfile)
    start = models.DateTimeField()
    end = models.DateTimeField(auto_now_add=True)