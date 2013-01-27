"""
This module contains unit tests for the schedule app.
"""

from django.test import TestCase
from schedule.models import Term, Timeslot, Show, Season
from schedule.utils import filler
from schedule.views import week
from django.utils import timezone
from datetime import timedelta


class FillEmptyRange(TestCase):
    """
    Tests whether the filling algorithm correctly handles an empty
    timeslot list.

    """

    fixtures = ['test_people', 'test_terms', 'filler_show']

    def setUp(self):
        self.timeslots = []
        self.duration = timedelta(hours=2)
        # 2011 should be in the terms fixture, and this should
        # correspond to a term date.
        self.past_time = timezone.now().replace(
            year=2011,
            month=11,
            day=1)
        self.future_time = self.past_time + self.duration

    def test_normal_fill(self):
        """
        Tests whether an attempt to fill an empty list returns a
        single filler slot spanning the entire requested range.

        """
        # First, some sanity checks on the test fixture
        self.assertIsNotNone(Term.of(self.past_time))
        self.assertIsNotNone(self.past_time)
        self.assertIsNotNone(self.future_time)
        self.assertIsNotNone(self.duration)

        filled = filler.fill(
            self.timeslots,
            self.past_time,
            self.future_time
        )
        # This should only have filled with one item
        self.assertEqual(len(filled), 1)

        filler_slot = filled[0]
        # ...which should be a Timeslot...
        self.assertIsInstance(filler_slot, Timeslot)
        # ... and should take up the entire required range.
        # The times might be out because filler slots try to set
        # their start/ends to end/starts of adjacent shows.
        self.assertTrue(filler_slot.start_time <= self.past_time)
        self.assertTrue(filler_slot.end_time() >= self.future_time)

    def test_negative_fill(self):
        """
        Tests whether an attempt to fill an empty list whose
        start time is after its end time results in an exception.

        """
        # First, some sanity checks on the test fixture
        self.assertIsNotNone(Term.of(self.past_time))
        self.assertIsNotNone(self.past_time)
        self.assertIsNotNone(self.future_time)
        self.assertIsNotNone(self.duration)

        with self.assertRaises(ValueError):
            filler.fill(
                self.timeslots,
                self.future_time,
                self.past_time
            )


class FillNormalRange(TestCase):
    """
    Tests whether the filling algorithm correctly handles a typical
    timeslot list.

    """

    fixtures = [
        'test_people',
        'test_terms',
        'filler_show',
        'test_shows'
    ]

    def setUp(self):
        assert (Show.objects.count() > 0)
        self.timeslots = list(Timeslot.objects.all())
        assert self.timeslots, \
            'No timeslots were loaded; please check test_shows.'

    def general_fill_tests(self, filled):
        """
        Performs common test assertions used in every subtest of
        this test run.

        """
        self.assertTrue(
            len(filled) >= len(self.timeslots),
            'Filler should not reduce the number of timeslots.'
        )

        for timeslot in self.timeslots:
            self.assertIn(
                timeslot,
                filled,
                'Filled timeslot missing some shows from the input.'
            )

        prev = None
        for timeslot in filled:
            if timeslot not in self.timeslots:
                self.assertEqual(
                    timeslot.show_type().name.lower(),
                    'filler',
                    'Filler incorrectly added non-filler timeslot.'
                )
            if prev:
                self.assertEqual(
                    timeslot.range_start(),
                    prev.range_end(),
                    'Filler has left a gap in between shows.'
                )
            prev = timeslot

    def test_normal_fill(self):
        """
        Tests whether the filling algorithm correctly fills a typical
        timeslot query in which neither end of the range requires
        pre or post-filling.

        """

        filled = filler.fill(
            self.timeslots,
            self.timeslots[0].range_start(),
            self.timeslots[-1].range_end()
        )

        self.general_fill_tests(filled)
        self.assertIs(
            self.timeslots[0],
            filled[0],
            'Filler mistakenly filled before first show.'
        )
        self.assertIs(
            self.timeslots[-1],
            filled[-1],
            'Filler mistakenly filled after first show.'
        )

    def test_pre_post_fill(self):
        """
        Tests whether the filling algorithm correctly fills a typical
        timeslot query in which both ends of the range require
        pre or post-filling.

        """

        hour = timedelta(hours=1)

        filled = filler.fill(
            self.timeslots,
            self.timeslots[0].range_start() - hour,
            self.timeslots[-1].range_end() + hour
        )

        self.general_fill_tests(filled)
        self.assertNotEqual(
            self.timeslots[0],
            filled[0],
            'Filler mistakenly did not fill before first show.'
        )
        self.assertNotEqual(
            self.timeslots[-1],
            filled[-1],
            'Filler mistakenly did not fill after first show.'
        )


class WeekSchedule(TestCase):
    """
    Tests various elements of the week schedule system.

    """
    def setUp(self):
        pass

    def test_to_monday(self):
        """
        Tests to ensure that the to_monday function returns a date
        representing some time in the Monday of the week of its
        input.

        """
        # 2018 is a common year beginning on Monday, so we can
        # look at January 2018 1-28 to test to_monday.
        for week_num in xrange(0, 4):
            monday = timezone.now().replace(
                year=2018,
                month=1,
                # Noting that the 1st of January 2018 is a Monday
                day=(week_num * 7) + 1
            )
            for day in xrange(1, 8):
                # Each day in the week should return monday as its
                # 'to_monday'.
                self.assertEqual(
                    monday,
                    week.to_monday(
                        monday.replace(day=(week_num * 7) + day)
                    ),
                    'Incorrect day returned as Monday.'
                )


class ShowScheduledSet(TestCase):
    """
    Tests whether the Show QuerySet provides two methods 'scheduled'
    and 'unscheduled' which filter to shows that have seasons with
    scheduled timeslots and no such seasons respectively.

    """
    fixtures = [
        'test_people',
        'test_terms',
        'filler_show',
        'test_shows'
    ]

    def setUp(self):
        pass

    def test_objects_set(self):
        shows = set(Show.objects.all())
        # NB: Filler show is counted (should be unscheduled)
        self.assertEqual(len(shows), 6)
        self.assertItemsEqual(
            shows,
            set(Show.objects.scheduled()) |
            set(Show.objects.unscheduled())
        )

    def test_scheduled_set(self):
        shows = set(Show.objects.scheduled())
        # Change this if the fixture is expanded.
        self.assertEqual(len(shows), 2)
        # Scheduled should contain all shows not in unscheduled.
        self.assertItemsEqual(
            shows,
            set(Show.objects.all()) -
            set(Show.objects.unscheduled())
        )
        # "Scheduled" shows should have at least one scheduled season
        for show in shows:
            self.assertGreater(
                show.season_set.all().scheduled().count(),
                0
            )

    def test_unscheduled_set(self):
        shows = set(Show.objects.unscheduled())
        # Change this if the fixture is expanded.
        # NB: Filler show is counted (should be unscheduled)
        self.assertEqual(len(shows), 4)
        # Unacheduled should contain all shows not in scheduled.
        self.assertItemsEqual(
            shows,
            set(Show.objects.all()) -
            set(Show.objects.scheduled())
        )
        # "Uncheduled" shows should have no seasons with timeslots
        for show in shows:
            self.assertEqual(
                show.season_set.all().scheduled().count(),
                0
            )


class SeasonScheduledSet(TestCase):
    """
    Tests whether the 'scheduled' manager correctly retrieves only
    seasons with scheduled seasons, whether the 'objects' manager
    correctly retrieves all seasons, and whether the 'unscheduled'
    manager retrieves only unscheduled seasons.

    """
    fixtures = [
        'test_people',
        'test_terms',
        'filler_show',
        'test_shows'
    ]

    def setUp(self):
        pass

    def test_objects_set(self):
        seasons = set(Season.objects.all())
        self.assertEqual(len(seasons), 5)
        self.assertItemsEqual(
            seasons,
            set(Season.objects.scheduled()) |
            set(Season.objects.unscheduled())
        )

    def test_scheduled_set(self):
        seasons = set(Season.objects.scheduled())
        # Change this if the fixture is expanded.
        self.assertEqual(len(seasons), 2)
        # Scheduled should contain all seasons not in unscheduled.
        self.assertItemsEqual(
            seasons,
            set(Season.objects.all()) -
            set(Season.objects.unscheduled())
        )
        # "Scheduled" seasons should have at least one timeslot
        for season in seasons:
            self.assertNotEqual(season.timeslot_set.count(), 0)

    def test_unscheduled_set(self):
        seasons = set(Season.objects.unscheduled())
        # Change this if the fixture is expanded.
        self.assertEqual(len(seasons), 3)
        # Unacheduled should contain all seasons not in scheduled.
        self.assertItemsEqual(
            seasons,
            set(Season.objects.all()) -
            set(Season.objects.scheduled())
        )
        # "Scheduled" seasons should have no timeslots
        for season in seasons:
            self.assertEqual(season.timeslot_set.count(), 0)


class ShowListableSet(TestCase):
    """
    Tests whether the Show QuerySet provides a method 'listable'
    that filters to shows that should filter only to shows that can
    be listed in public show lists.

    """
    fixtures = [
        'test_people',
        'test_terms',
        'filler_show',
        'test_shows'
    ]

    def test_listable(self):
        shows = Show.objects.listable()
        scheduled = Show.objects.scheduled()
        unscheduled = Show.objects.unscheduled()
        for show in shows:
            self.assertIn(show, scheduled)
            self.assertTrue(show.show_type.has_showdb_entry)
        for show in unscheduled:
            self.assertNotIn(show, shows)
