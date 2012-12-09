"""Models concerning URY shows."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

# All tables here, unless explicitly stated, are in the 'schedule'
# schema in URY.

from django.conf import settings
from django.db import models

from lass_utils.mixins import SubmittableMixin
from lass_utils.mixins import EffectiveRangeMixin
from lass_utils.models.type import Type

from metadata.mixins import MetadataSubjectMixin
from metadata.models.text import TextMetadata
from metadata.models.image import ImageMetadata

from uryplayer.models import PodcastLink

from people.models import Person
from people.mixins import ApprovableMixin
from people.mixins import CreatableMixin
from people.mixins import CreditableMixin

from schedule.models import Location


class ShowType(Type):
    """
    A type of show in the URY schedule.

    """
    if hasattr(settings, 'SHOW_TYPE_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.SHOW_TYPE_DB_ID_COLUMN
        )
    public = models.BooleanField(default=True)
    has_showdb_entry = models.BooleanField(default=True)
    can_be_messaged = models.BooleanField(
        default=False,
        help_text="""If this is True, then the show can be messaged
            through the main page message form.

            """
    )

    class Meta(Type.Meta):
        if hasattr(settings, 'SHOW_TYPE_DB_TABLE'):
            db_table = settings.SHOW_TYPE_DB_TABLE
        app_label = 'schedule'


class ShowLocation(EffectiveRangeMixin,
                   CreatableMixin,
                   ApprovableMixin):
    """
    A mapping of shows to their locations.

    """
    if hasattr(settings, 'SHOW_LOCATION_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.SHOW_LOCATION_DB_ID_COLUMN
        )
    show = models.ForeignKey(
        'Show',
        db_column='show_id'
    )
    location = models.ForeignKey(
        Location,
        db_column='location_id'
    )

    class Meta(EffectiveRangeMixin.Meta):
        if hasattr(settings, 'SHOW_LOCATION_DB_TABLE'):
            db_table = settings.SHOW_LOCATION_DB_TABLE
        app_label = 'schedule'


class Show(MetadataSubjectMixin,
           SubmittableMixin,
           CreatableMixin,
           CreditableMixin):
    """
    A show in the URY schedule.

    URY show objects represent the part of a show that is constant
    across any time-slots it is scheduled into: the show's type,
    creation date, credited people, and so on.

    """
    if hasattr(settings, 'SHOW_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.SHOW_DB_ID_COLUMN
        )
    _SHOW_TYPE_KWARGS = {}
    if hasattr(settings, 'SHOW_DB_TYPE_COLUMN'):
        _SHOW_TYPE_KWARGS['db_column'] = settings.SHOW_DB_TYPE_COLUMN
    show_type = models.ForeignKey(
        ShowType,
        help_text="""The show type, which affects whether or not the
            show appears in the public schedule, amongst other things.
            """,
        **_SHOW_TYPE_KWARGS
    )
    people = models.ManyToManyField(
        Person,
        through='ShowCredit'
    )
    locations = models.ManyToManyField(
        Location,
        through=ShowLocation
    )

    class Meta:
        if hasattr(settings, 'SHOW_DB_TABLE'):
            db_table = settings.SHOW_DB_TABLE
        ordering = ['show_type', '-date_submitted']
        app_label = 'schedule'

    @classmethod
    def make_foreign_key(cls):
        """
        Shortcut for creating a field that links to a show.

        """
        _FKEY_KWARGS = {}
        if hasattr(settings, 'SHOW_DB_FKEY_COLUMN'):
            _FKEY_KWARGS['db_column'] = settings.SHOW_DB_FKEY_COLUMN
        return models.ForeignKey(
            cls,
            help_text='The show associated with this item.',
            **_FKEY_KWARGS
        )

    ## OVERRIDES ##

    def __unicode__(self):
        return u'{0} ({1})'.format(self.title, self.id)

    @models.permalink
    def get_absolute_url(self):
        return ('show_detail', [str(self.id)])

    def metadata_strands(self):
        return {
            'text': self.showtextmetadata_set,
            'image': self.showimagemetadata_set,
        }

    def credits_set(self):
        return self.showcredit_set

    def block(self):
        """Returns the block that the show is in, if any.

        This will return a Block object if a block is matched, or
        None if there wasn't one (one can associate to Block.default()
        in this case, if a block is needed).

        For seasons and timeslots, use their block() methods instead
        so as to pull in season and timeslot specific matching rules.

        """
        # Show rules take precedence
        block_matches = self.blockshowrule_set.order_by(
            '-block__priority')
        if block_matches.exists():
            block = block_matches[0].block
        else:
            block = None
        return block


ShowTextMetadata = TextMetadata.make_model(
    Show,
    'schedule',
    'ShowTextMetadata',
    getattr(
        settings, 'SHOW_TEXT_METADATA_DB_TABLE',
        None
    ),
    getattr(
        settings, 'SHOW_TEXT_METADATA_DB_ID_COLUMN',
        None
    ),
    help_text='The show associated with this textual metadata.',
    fkey=Show.make_foreign_key(),
)


ShowImageMetadata = ImageMetadata.make_model(
    Show,
    'schedule',
    'ShowImageMetadata',
    getattr(
        settings, 'SHOW_IMAGE_METADATA_DB_TABLE',
        None
    ),
    getattr(
        settings, 'SHOW_IMAGE_METADATA_DB_ID_COLUMN',
        None
    ),
    help_text='The show associated with this image metadata.',
    fkey=Show.make_foreign_key(),
)


ShowPodcastLink = PodcastLink.make_model(
    Show,
    'schedule',
    'ShowPodcastLink',
    getattr(settings, 'SHOW_PODCAST_LINK_DB_TABLE', None),
    getattr(settings, 'SHOW_PODCAST_LINK_DB_ID_COLUMN', None),
    help_text='The show this podcast link is attached to.',
    fkey=Show.make_foreign_key()
)
