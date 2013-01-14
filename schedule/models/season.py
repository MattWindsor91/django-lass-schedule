"""Models concerning URY show seasons."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.conf import settings
from django.db import models

from lass_utils.mixins import SubmittableMixin

from metadata.models.text import TextMetadata
from metadata.mixins import MetadataSubjectMixin

from people.mixins import CreatableMixin
from people.mixins import CreditableMixin

from schedule.models.term import Term
from schedule.models.show import Show


class Season(MetadataSubjectMixin,
             SubmittableMixin,
             CreatableMixin,
             CreditableMixin):
    """
    A season of a URY show.

    Seasons map onto terms of scheduled timeslots for a show.

    """
    if hasattr(settings, 'SEASON_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.SEASON_DB_ID_COLUMN
        )

    show = Show.make_foreign_key()
    term = Term.make_foreign_key()

    class Meta:
        if hasattr(settings, 'SEASON_DB_TABLE'):
            db_table = settings.SEASON_DB_TABLE
        verbose_name = 'show season'
        app_label = 'schedule'

    ## MAGIC METHODS ##

    def __unicode__(self):
        try:
            show = self.show
        except Show.DoesNotExist:
            show = '(No Show)'
        try:
            term = self.term
        except Term.DoesNotExist:
            term = '(No Term)'
        return u'[{0}] -> {1}'.format(show, term)

    ## OVERRIDES ##

    def metadata_strands(self):
        return {
            'text': self.seasontextmetadata_set
        }

    def metadata_parent(self):
        return self.show

    def credits_set(self):
        """Provides the set of this season's credits."""
        return self.show.credits_set()

    @models.permalink
    def get_absolute_url(self):
        """Retrieves the absolute URL through which a timeslot can be
        found on the website.

        """
        return ('season_detail', (), {
            'pk': self.show.id,
            'season_num': self.number()})

    ## ADDITIONAL METHODS ##

    def number(self):
        """Returns the relative number of this season, with the first
        season of the attached show returning a number of 1.

        """
        number = None
        for index, season in enumerate(self.show.season_set.all()):
            if season.id == self.id:
                number = index + 1  # Note that this can never be 0
                break
        assert number, "Season not in its show's season set."
        return number

    def block(self):
        """Returns the block that the season is in, if any.

        This will return a Block object if a block is matched, or
        None if there wasn't one (one can associate to Block.default()
        in this case, if a block is needed).

        For timeslots, use their block() methods instead so as to pull
        in timeslot specific matching rules.

        """
        # Show rules take precedence
        show_block = self.show.block()
        if show_block is None:
            # TODO: add direct rules for season
            # Now do season based checks
            #block_show_matches = self.blockshowrule_set.filter(
            #    show=self).order_by('-priority')
            #if block_show_matches.exists():
            #block = block_show_matches[0]
            #else:
            block = None
        else:
            block = show_block
        return block

    @classmethod
    def make_foreign_key(cls):
        """
        Shortcut for creating a field that links to a season, given
        the source model's metadata class.

        """
        kwargs = {}
        if hasattr(settings, 'SEASON_DB_FKEY_COLUMN'):
            kwargs['db_column'] = settings.SEASON_DB_FKEY_COLUMN
        return models.ForeignKey(
            cls,
            help_text='The season associated with this item.',
            **kwargs
        )


SeasonTextMetadata = TextMetadata.make_model(
    Season,
    'schedule',
    'SeasonTextMetadata',
    getattr(
        settings, 'SEASON_TEXT_METADATA_DB_TABLE',
        None
    ),
    getattr(
        settings, 'SEASON_TEXT_METADATA_DB_ID_COLUMN',
        None
    ),
    fkey=Season.make_foreign_key(),
)
