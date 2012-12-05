"""Models concerning credits on URY shows."""

# IF YOU'RE ADDING CLASSES TO THIS, DON'T FORGET TO ADD THEM TO
# __init__.py

from django.conf import settings

from schedule.models.show import Show
from people.models import Credit

ShowCredit = Credit.make_model(
    Show,
    'schedule',
    'ShowCredit',
    getattr(
        settings, 'SHOW_CREDIT_DB_TABLE',
        None
    ),
    getattr(
        settings, 'SHOW_CREDIT_DB_ID_COLUMN',
        None
    ),
    getattr(
        settings, 'SHOW_CREDIT_DB_FKEY_COLUMN',
        None
    ),
    'The show associated with this credit.',
)
