"""Models for rules mapping blocks directly to schedule items."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.db import models
from urysite import model_extensions as exts
from schedule.models.show import Show
from schedule.models.block import Block

# Why are these in their own file?  It makes things a little less
# cluttered in block, and eliminates circular dependencies.


class BlockShowRule(models.Model):
    """
    A block matching rule that matches the attached show only.

    This rule takes precedence over all other rules, except any
    directly matching timeslots.

    """

    class Meta:
        db_table = 'block_show_rule'  # In schema 'schedule'
        managed = False  # It's in another schema, so can't manage
        app_label = 'schedule'

    def __unicode__(self):
        return u'{0} -> {1}'.format(self.show, self.block)

    id = exts.primary_key_from_meta(Meta)

    block = models.ForeignKey(
        Block,
        help_text='The block this rule matches against.')

    show = models.ForeignKey(
        Show,
        help_text='The show this rule assigns a block to.')
