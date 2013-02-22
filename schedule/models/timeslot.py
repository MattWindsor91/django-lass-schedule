"""Models concerning URY schedule timeslots."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from datetime import timedelta as td

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet

import timedelta

from lass_utils.mixins import DateRangeMixin

from metadata.models.text import TextMetadata
from metadata.mixins import MetadataSubjectMixin

from model_utils.managers import PassThroughManager

from people import mixins as p_mixins

from schedule.models.show import ShowLocation
from schedule.models.season import Season


class TimeslotQuerySet(QuerySet):
    """
    Custom QuerySet allowing date range-based filtering.

    """
    def public(self):
        """Filters down to timeslots that are publicly available."""
        return self.filter(season__in=Season.objects.public())

    def private(self):
        """Filters down to timeslots that are not publicly available."""
        return self.filter(season__in=Season.objects.private())

    def in_range(self, from_date, to_date):
        """Filters towards a QuerySet of items in this QuerySet that are
        effective during the given date range.

        The items must cover the entire range.

        Items with an 'effective_from' of NULL will be discarded;
        items with an 'effective_to' of NULL will be treated as if
        their effective_to is infinitely far in the future.

        If queryset is given, it will be filtered with the above condition;
        else the entire object set will be considered.
        """
        # Note that filter throws out objects with fields set to
        # NULL whereas exclude does not.
        return self.after(from_date).before(to_date)

    def after(self, date):
        """Filters to shows that occur partly or wholly after date."""
        return self.filter(start_time__gt=date - models.F('duration'))

    def before(self, date):
        """Filters to shows that occur partly or wholly before date."""
        return self.filter(start_time__lt=date)

    def in_day(self, day_start):
        """
        Filters down to timeslots between `day_start` and the point
        exactly one day after, exclusive.
        """
        return self.in_range(day_start, day_start + td(days=1))

    def in_week(self, week_start):
        """
        Filters down to timeslots between `week_start` and the point
        exactly one week after, exclusive.
        """
        return self.in_range(week_start, week_start + td(weeks=1))

    def at(self, date):
        """
        Wrapper around 'in_range' that retrieves items effective
        at the given moment in time.
        """
        return self.in_range(date, date)


class Timeslot(p_mixins.ApprovableMixin,
               p_mixins.CreatableMixin,
               p_mixins.CreditableMixin,
               DateRangeMixin,
               MetadataSubjectMixin):
    """
    A slot in the URY schedule allocated to a show.

    URY timeslots can overlap, because not all timeslots represent
    on-air shows (the schedule system is used to schedule demos,
    in-studio recordings, and outside broadcasts as well as in-studio
    shows).  Because of this, a timeslot CANNOT safely be uniquely
    identified from its show and time range - use the timeslot ID.
    """
    if hasattr(settings, 'TIMESLOT_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.TIMESLOT_DB_ID_COLUMN
        )
    season = Season.make_foreign_key()
    start_time = models.DateTimeField(
        db_column='start_time',
        help_text='The date and time of the start of this timeslot.'
    )
    duration = timedelta.TimedeltaField(
        db_column='duration',
        default='1:00:00',
        help_text='The duration of the timeslot.'
    )
    objects = PassThroughManager.for_queryset_class(TimeslotQuerySet)()

    class Meta:
        if hasattr(settings, 'TIMESLOT_DB_TABLE'):
            db_table = settings.TIMESLOT_DB_TABLE
        verbose_name = 'show timeslot'
        get_latest_by = 'start_time'
        ordering = ['start_time']
        app_label = 'schedule'

    ## PROPERTIES ##

    @property
    def end_time(self):
        """Calculates the end time of this timeslot."""
        return self.start_time + self.duration

    @property
    def show_type(self):
        """Returns the type of this timeslot's show."""
        if not hasattr(self, '_show_type'):
            self._show_type = self.season.show.show_type
        return self._show_type

    @property
    def has_showdb_entry(self):
        """Returns whether the timeslot has an entry in the show database."""
        return self.show_type.has_showdb_entry

    @property
    def is_collapsible(self):
        """Returns whether this timeslot can collapse in the schedule."""
        return self.show_type.is_collapsible

    @property
    def can_be_messaged(self):
        """Returns whether this timeslot is messagable via the website."""
        return self.show_type.can_be_messaged

    @property
    def location(self):
        """Returns the location the timeslot was broadcasted from.

        If no location is on file for the timeslot's time, None is
        returned.
        """
        locations = self.season.show.showlocation_set.at(self.start_time)
        try:
            result = locations.latest().location
        except ShowLocation.DoesNotExist:
            result = None
        return result

    ## MAGIC METHODS ##

    def __unicode__(self):
        """Provides a Unicode representation of this timeslot."""
        try:
            season = self.season
        except Season.DoesNotExist:
            season = '(No Season)'
        return u'{0} ({1} to {2})'.format(
            season,
            self.start_time,
            self.end_time
        )

    ## OVERRIDES ##

    # MetadataSubjectMixin

    def metadata_strands(self):
        """Provides the sets of this timeslot's metadata."""
        return {
            'text': self.timeslottextmetadata_set
        }

    def metadata_parent(self):
        """Provides the metadata inheritance parent of this timeslot.

        """
        return self.season

    # CreditableMixin

    def credits_set(self):
        """Provides the set of this timeslot's credits."""
        return self.season.credits_set()

    # DateRangeMixin

    def range_start(self):
        """Retrieves the start of this timeslot's date range."""
        return self.start_time

    def range_end(self):
        """Retrieves the end of this timeslot's date range."""
        return self.end_time

    def range_duration(self):
        """Retrieves the duration of this timeslot's date range."""
        return self.duration

    @classmethod
    def range_start_filter_arg(cls, inequality, value):
        """Given a filter inequality and a value to compare against,
        returns a tuple of the keyword argument and value that can
        be used to represent that inequality against the range start
        time in a filter.

        """
        return (
            u'__'.join(u'start_time', inequality),
            value
        )

    @classmethod
    def range_end_filter_arg(cls, inequality, value):
        """Given a filter inequality and a value to compare against,
        returns a tuple of the keyword argument and value that can
        be used to represent that inequality against the range end
        time in a filter.

        """
        return (
            u'__'.join(u'duration', inequality),
            value - models.F('start_time')
        )

    # Model

    @models.permalink
    def get_relative_number_url(self):
        """Retrieves the relative-number based absolute URL through which a
        timeslot can be found on the website.

        This is nicer than get_absolute_url, but very costly in terms of
        queries.
        """
        return (
            'timeslot_detail_relative',
            (),
            {
                'pk': self.season.show.id,
                'season_num': self.season.number,
                'timeslot_num': self.number
            }
        )

    @models.permalink
    def get_absolute_url(self):
        """Retrieves the absolute URL through which a timeslot can be
        found on the website.

        """
        return ('timeslot_detail', (), {'pk': self.pk})

    @property
    def number(self):
        """Returns the relative number of this timeslot, with the
        first timeslot of the attached season returning a number of 1.

        """
        if not hasattr(self, '_number'):
            self._number = list(
                self.season.timeslot_set.values_list('pk', flat=True)
            ).index(self.pk) + 1
        return self._number

    @classmethod
    def make_foreign_key(cls):
        """
        Shortcut for creating a field that links to a timeslot, given
        the source model's metadata class.

        """
        kwargs = {}
        if hasattr(settings, 'TIMESLOT_DB_FKEY_COLUMN'):
            kwargs['db_column'] = settings.TIMESLOT_DB_FKEY_COLUMN
        return models.ForeignKey(
            cls,
            help_text='The timeslot associated with this item.',
            **kwargs
        )


TimeslotTextMetadata = TextMetadata.make_model(
    Timeslot,
    'schedule',
    'TimeslotTextMetadata',
    getattr(
        settings, 'TIMESLOT_TEXT_METADATA_DB_TABLE',
        None
    ),
    getattr(
        settings, 'TIMESLOT_TEXT_METADATA_DB_ID_COLUMN',
        None
    ),
    fkey=Timeslot.make_foreign_key(),
)
