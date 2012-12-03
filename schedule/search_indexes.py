"""Schedule app search configuration for Haystack."""

import datetime
from haystack.indexes import *
from haystack import site
from schedule.models import Show


class ShowIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    title = CharField(model_attr='title')
    description = CharField(model_attr='description')
    people = MultiValueField()

    def prepare_people(self, obj):
        unordered = obj.people.all()
        people = unordered.order_by(
            'last_name', 'first_name')
        return [person.id for person in people]


site.register(Show, ShowIndex)
