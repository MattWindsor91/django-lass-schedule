"""A location a show can be broadcast from."""

from django.db import models
from urysite import model_extensions as exts


class Location(models.Model):
    """A location in URY.

    Locations are generally used to tag the origins of shows, for
    purposes such as webcam auto-configuration and location clash
    avoidance.

    """

    class Meta:
        db_table = 'location'  # in schema 'schedule'
        app_label = 'schedule'

    id = exts.primary_key_from_meta(Meta)

    name = models.TextField(
        db_column='location_name',
        help_text='The human-readable name of this location.')
