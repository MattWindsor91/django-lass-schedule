"""
This module contains unit tests for the schedule app.
"""

from django.test import TestCase
from schedule.models import Term, Timeslot, Show
from schedule.utils import filler
from schedule.views import week
from django.utils import timezone
from datetime import timedelta


class FillEmptyRange(TestCase):
    """
    Tests whether the filling algorithm correctly handles an empty
    timeslot list.

    """

    fixtures = ['test_people.json', 'test_terms.json', 'filler_show.json']

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
        'test_people.json',
        'test_terms.json',
        'filler_show.json',
        'test_shows.json'
    ]

    def setUp(self):
        assert (Show.objects.count() > 0)
        self.timeslots = list(Timeslot.objects.all())
        assert self.timeslots, \
            'No timeslots were loaded; please check test_shows.json.'

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
