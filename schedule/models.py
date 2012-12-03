"""Models for the URY schedule.

Except where explicitly stated otherwise, the database tables in
this module are in the 'schedule' schema in URY.

"""

from django.db import models
from people.models import Person
from urysite import model_extensions as exts


#################################
## Schedule entity ABCs/mixins ##
#################################

class ScheduleEntity(models.Model):
    """Abstract class for all creatable schedule entities.

    This class captures the common features of all creatable
    schedule entities, namely the inclusion of creator and approver
    links.

    """

    class Meta:
        abstract = True

    # Override this when implementing this ABC
    entity_name = 'schedule entity'

    creator = models.ForeignKey(
        Creator,
        db_column='memberid',
        help_text='The creator of this %s.' % entity_name)

    approver = models.ForeignKey(
        Approver,
        null=True,
        db_column='approverid',
        help_text="""The approver of this %s.

        If not specified, the entity has not been approved.

        """ % entity_name)
