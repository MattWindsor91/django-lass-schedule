"""Models concerning URY terms."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.conf import settings
from django.db import models


class Term(models.Model):
    """
    A university term.

    Because University Radio York is a student radio station, its
    timetables are organised along University of York term
    boundaries.  This means that seasons are delineated by the
    terms that they cover, which are represented in the database
    using this model.

    """
    if hasattr(settings, 'TERM_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.TERM_DB_ID_COLUMN
        )

    start_date = models.DateTimeField(
        db_column='start')
    end_date = models.DateTimeField(
        db_column='finish')
    name = models.CharField(
        max_length=10,
        db_column='descr')

    class Meta:
        if hasattr(settings, 'TERM_DB_TABLE'):
            db_table = settings.TERM_DB_TABLE
        app_label = 'schedule'
        get_latest_by = 'start_date'
        ordering = ['start_date']

    def __unicode__(self):
        """
        Returns a human-readable representation of this term.

        The representation is of the form "NAME Term YEAR", where
        Name is Autumn, Spring or Summer and YEAR is the academic
        year in nnnn/nn+1 format, for example 2011/12.

        """
        year = self.academic_year()
        return u'{} Term {}/{}'.format(
            self.name,
            year,
            (year + 1) % 100
        )

    def academic_year(self):
        """Returns the academic year of this term.

        """
        # Heuristic: if a term starts before September, then
        # it'll be the Spring or Summer of the academic year
        # that started the previous year.
        return (self.start_date.year
                if self.start_date.month >= 9
                else self.start_date.year - 1)

    @classmethod
    def of(cls, date):
        """
        Returns the term of the given date, or None if the date
        does not lie in any known term.

        """
        query = cls.objects.filter(
            start_date__lte=date,
            end_date__gt=date
        )
        try:
            result = query.latest()
        except Term.DoesNotExist:
            result = None
        return result

    @classmethod
    def before(cls, date):
        """Assuming the given date does not belong in a term, returns
        the last term to occur before the date.

        This can be used to find out which holiday the date is in,
        if any.

        """
        query = cls.objects.filter(
            start_date__lte=date,
            end_date__lte=date
        )
        try:
            result = query.latest()
        except Term.DoesNotExist:
            result = None
        return result

    @classmethod
    def make_foreign_key(cls):
        """
        Shortcut for creating a field that links to a show, given the
        source model's metadata class.

        """
        _FKEY_KWARGS = {}
        if hasattr(settings, 'TERM_DB_FKEY_COLUMN'):
            _FKEY_KWARGS['db_column'] = settings.TERM_DB_FKEY_COLUMN
        return models.ForeignKey(
            cls,
            help_text='The term associated with this item.',
            **_FKEY_KWARGS
        )
