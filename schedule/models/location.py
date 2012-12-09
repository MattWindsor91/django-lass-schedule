"""A location a show can be broadcast from."""

from django.conf import settings
from django.db import models


class Location(models.Model):
    """
    A location in URY.

    Locations are generally used to tag the origins of shows, for
    purposes such as webcam auto-configuration and location clash
    avoidance.

    """
    if hasattr(settings, 'LOCATION_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.LOCATION_DB_ID_COLUMN
        )
    name = models.TextField(
        db_column='location_name',
        help_text='The human-readable name of this location.'
    )

    class Meta:
        if hasattr(settings, 'LOCATION_DB_TABLE'):
            db_table = settings.LOCATION_DB_TABLE
        app_label = 'schedule'
