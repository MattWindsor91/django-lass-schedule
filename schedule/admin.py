from django.contrib import admin

from metadata.admin_base import TextMetadataInline

from schedule.models import Block
from schedule.models import BlockShowRule, BlockRangeRule
from schedule.models import Show, ShowCredit
from schedule.models import ShowTextMetadata
from schedule.models import Season
from schedule.models import Timeslot


## BlockShowRule ##

class BlockShowRuleInline(admin.TabularInline):
    model = BlockShowRule


class BlockRangeRuleInline(admin.TabularInline):
    model = BlockRangeRule


## Block ##

class BlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'priority')
    inlines = [
        BlockShowRuleInline
    ]


## Timeslot ##

class TimeslotAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'
    list_display = ('season', 'start_time', 'duration')


class TimeslotInline(admin.TabularInline):
    model = Timeslot


## ShowCredit ##

class ShowCreditInline(admin.TabularInline):
    model = Show.people.through


class ShowCreditAdmin(admin.ModelAdmin):
    list_display = ('element', 'person', 'credit_type')


## Season ##

class SeasonAdmin(admin.ModelAdmin):
    model_display = ('show', 'term')
    inlines = [
        TimeslotInline
    ]


class SeasonInline(admin.TabularInline):
    model = Season


## Show ##

class ShowTextMetadataInline(TextMetadataInline):
    model = ShowTextMetadata


class ShowAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_submitted'
    list_display = ('title', 'description', 'date_submitted')
    list_filter = ('show_type',)
    inlines = [
        SeasonInline,
        ShowCreditInline,
        ShowTextMetadataInline
    ]

    # These are needed because title and description are pseudo
    # attributes exported through the metadata system.

    def title(self, obj):
        return obj.title

    def description(self, obj):
        return obj.description


def register(site):
    """
    Registers the schedule admin hooks with an admin site.

    """
    site.register(Show, ShowAdmin)
    site.register(Block, BlockAdmin)
    site.register(Timeslot, TimeslotAdmin)
    site.register(ShowCredit, ShowCreditAdmin)
    site.register(Season, SeasonAdmin)
