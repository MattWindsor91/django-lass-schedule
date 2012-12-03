from schedule.models import Block
from schedule.models import BlockShowRule, BlockRangeRule
from schedule.models import Show, ShowCredit
from schedule.models import Season
from schedule.models import Timeslot
from django.contrib import admin


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


admin.site.register(Block, BlockAdmin)


## Timeslot ##

class TimeslotAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'
    list_display = ('season', 'start_time', 'duration')


class TimeslotInline(admin.TabularInline):
    model = Timeslot


admin.site.register(Timeslot, TimeslotAdmin)


## ShowCredit ##

class ShowCreditInline(admin.TabularInline):
    model = Show.people.through


class ShowCreditAdmin(admin.ModelAdmin):
    list_display = ('show', 'person', 'credit_type')


admin.site.register(ShowCredit, ShowCreditAdmin)


## Season ##

class SeasonAdmin(admin.ModelAdmin):
    model_display = ('show', 'term')
    inlines = [
        TimeslotInline
    ]


class SeasonInline(admin.TabularInline):
    model = Season


admin.site.register(Season, SeasonAdmin)


## Show ##

class ShowAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_submitted'
    list_display = ('title', 'description', 'date_submitted')
    list_filter = ('show_type',)
    inlines = [
        SeasonInline,
        ShowCreditInline
    ]


admin.site.register(Show, ShowAdmin)
