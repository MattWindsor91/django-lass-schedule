"""Models concerning credits on the URY schedule."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.db import models
from urysite import model_extensions as exts
from schedule.models.show import Show
from people.models import CreditType, Person, Creator, Approver


class ShowCredit(models.Model):
    """The intermediate model for the Show<->Person relationship.

    The rationale for the naming is that a ShowCredit is a "credit"
    (in the "film credits" sense) for a person's role on a given
    show.

    """

    class Meta:
        db_table = 'show_credit'  # In schema "schedule"
        managed = False  # Can't manage, in non-public schema
        app_label = 'schedule'
        ordering = ['credit_type__name']

    def __unicode__(self):
        return self.person.full_name()

    id = exts.primary_key_from_meta(Meta)

    show = models.ForeignKey(
        Show,
        db_column='show_id',
        help_text='The show that the person is being credited for.')

    person = models.ForeignKey(
        Person,
        db_column='creditid',
        help_text='The person being credited for working on a show.',
        related_name='show_credits_set')

    creator = models.ForeignKey(
        Creator,
        db_column='memberid',
        help_text='The person who created the credit.',
        related_name='created_show_credits_set')

    approver = models.ForeignKey(
        Approver,
        null=True,
        db_column='approvedid',
        help_text='The person who approved the credit, if any.',
        related_name='approved_show_credits_set')

    credit_type = models.ForeignKey(
        CreditType,
        db_column='credit_type_id',
        help_text='The type of credit the person is assigned.')

    effective_from = models.DateTimeField(
        db_column='effective_from',
        help_text='The date from which this credit applies.')

    effective_to = models.DateTimeField(
        db_column='effective_to',
        null=True,
        help_text='The date on which this credit ceases to apply, if any.')
