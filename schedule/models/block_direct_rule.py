"""Models for rules mapping blocks directly to schedule items."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.conf import settings
from django.db import models

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
    if hasattr(settings, 'BLOCK_SHOW_RULE_DB_ID_COLUMN'):
        id = models.AutoField(
            primary_key=True,
            db_column=settings.BLOCK_SHOW_RULE_DB_ID_COLUMN
        )
    block = models.ForeignKey(
        Block,
        help_text='The block this rule matches against.'
    )
    show = models.ForeignKey(
        Show,
        help_text='The show this rule assigns a block to.'
    )

    class Meta:
        if hasattr(settings, 'BLOCK_SHOW_RULE_DB_TABLE'):
            db_table = settings.BLOCK_SHOW_RULE_DB_TABLE
        app_label = 'schedule'

    def __unicode__(self):
        return u'{0} -> {1}'.format(self.show, self.block)
