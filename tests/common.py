#  python-holidays
#  ---------------
#  A fast, efficient Python library for generating country, province and state
#  specific sets of holidays on the fly. It aims to make determining whether a
#  specific date is a holiday as fast and flexible as possible.
#
#  Authors: dr-prodigy <dr.prodigy.github@gmail.com> (c) 2017-2023
#           ryanss <ryanssdev@icloud.com> (c) 2014-2017
#  Website: https://github.com/dr-prodigy/python-holidays
#  License: MIT (see LICENSE file)

import os
import unittest
import warnings
from datetime import date
from typing import Generator

from dateutil.parser import parse

from holidays import HolidayBase
from holidays.calendars.gregorian import SUN

PYTHON_VERSION = (3, 11)


class TestCase(unittest.TestCase):
    """Base class for python-holidays test cases."""

    @classmethod
    def setUpClass(cls, test_class=None, years=None, years_non_observed=None):
        super().setUpClass()

        if test_class is None:
            return None

        cls.test_class = test_class

        if (
            getattr(test_class, "default_language") is not None
            # Normally 2-6 letters (e.g., en, pap, en_US, pap_AW).
            and 2 > len(test_class.default_language) > 6
        ):
            raise ValueError(f"`{test_class.__name__}.default_language` value is invalid.")

        if getattr(test_class, "default_language") is not None:
            cls.set_language(test_class, test_class.default_language)

        if years:
            cls.holidays = test_class(years=years)
        if years_non_observed:
            cls.holidays_non_observed = test_class(observed=False, years=years_non_observed)

    def setUp(self):
        super().setUp()

        if getattr(self.test_class, "default_language") is not None:
            self.set_language(self.test_class.default_language)

        if not hasattr(self, "holidays"):
            self.holidays = self.test_class()

        if not hasattr(self, "holidays_non_observed"):
            self.holidays_non_observed = self.test_class(observed=False)

    def set_language(self, language):
        os.environ["LANGUAGE"] = language

    def _parse_arguments(
        self, args, expand_items=True, instance_name="holidays", raise_on_empty=True
    ):
        item_args = args
        instance = None

        if args and issubclass(args[0].__class__, HolidayBase):
            instance = args[0]
            item_args = args[1:]
        else:
            try:
                instance = getattr(self, instance_name)
                self.assertTrue(
                    issubclass(instance.__class__, HolidayBase),
                    f"The `self.{instance_name}` must be a `HolidayBase` subclass.",
                )
            except AttributeError:
                raise ValueError(
                    "Either pass a holidays object (`HolidayBase` subclass) "
                    "as a first argument or initialize your `TestCase` class "
                    "properly with `setUpClass()` method."
                )

        items = []
        if expand_items:
            for item_arg in item_args:
                if isinstance(item_arg, (list, set, tuple)):
                    items.extend(item_arg)
                elif isinstance(item_arg, (Generator, range)):
                    items.extend(tuple(item_arg))
                else:
                    items.append(item_arg)
        else:
            items.extend(item_args)

        if instance_name == "holidays":
            self.assertTrue(instance.observed)
        else:
            self.assertFalse(instance.observed)

        if raise_on_empty and len(items) == 0:
            raise ValueError("The test argument sequence is empty")

        return instance, items

    def _verify_type(self, holidays):
        self.assertTrue(
            issubclass(holidays.__class__, HolidayBase),
            "`holidays` object must be a subclass of `HolidayBase`",
        )

    def assertCountryAliases(self, cls, alpha_2, alpha_3):
        """Assert country aliases match."""
        self.assertTrue(
            issubclass(cls, HolidayBase),
            "Country holidays object must be a subclass of `HolidayBase`",
        )

        type_error_message = "Country alias object must be a subclass of the country class."
        for alias in (alpha_2, alpha_3):
            self.assertIsNotNone(alias, type_error_message)
            self.assertTrue(issubclass(alias, cls), type_error_message)

        length_error_message = (
            "This method accepts exactly 3 arguments "
            "in this specific order: country base class, country alpha-2 "
            "alias, and country alpha-3 alias. For example: "
            "`self.assertCountryAliases(UnitedStates, US, USA)`"
        )
        if len(alpha_2.__name__) != 2:
            raise ValueError(
                f"{length_error_message}. Alias `{alpha_2.__name__}` doesn't "
                "look like alpha-2 country code."
            )

        if len(alpha_3.__name__) != 3:
            raise ValueError(
                f"{length_error_message}. Alias `{alpha_3.__name__}` doesn't "
                "look like alpha-3 country code."
            )

    def assertDeprecatedSubdivisions(self, message):
        warnings.simplefilter("always", category=DeprecationWarning)
        for subdiv in self.test_class._deprecated_subdivisions:
            with warnings.catch_warnings(record=True) as ctx:
                self.test_class(subdiv=subdiv)
                warning = ctx[0]
                self.assertTrue(issubclass(warning.category, DeprecationWarning))
                self.assertIn(message, str(warning.message))

    # Holiday.
    def _assertHoliday(self, instance_name, *args):
        """Helper: assert each date is a holiday."""
        holidays, dates = self._parse_arguments(args, instance_name=instance_name)
        self._verify_type(holidays)

        for dt in dates:
            self.assertIn(dt, holidays, dt)

    def assertHoliday(self, *args):
        """Assert each date is a holiday."""
        self._assertHoliday("holidays", *args)

    def assertNonObservedHoliday(self, *args):
        """Assert each date is a non-observed holiday."""
        self._assertHoliday("holidays_non_observed", *args)

    # Holiday dates.
    def _assertHolidayDates(self, instance_name, *args):
        """Helper: assert holiday dates exactly match expected dates."""
        holidays, dates = self._parse_arguments(args, instance_name=instance_name)
        self._verify_type(holidays)

        # Check one by one for descriptive error messages.
        for dt in dates:
            self.assertIn(dt, holidays, dt)

        self.assertEqual(len(dates), len(holidays.keys()), set(dates).difference(holidays.keys()))

    def assertHolidayDates(self, *args):
        """Assert holiday dates exactly match expected dates."""
        self._assertHolidayDates("holidays", *args)

    def assertNonObservedHolidayDates(self, *args):
        """Assert holiday dates exactly match expected dates."""
        self._assertHolidayDates("holidays_non_observed", *args)

    # Holiday name.
    def _assertHolidayName(self, name, instance_name, *args):
        """Helper: assert either a holiday with a specific name exists or
        each holiday name matches an expected one depending on the args nature.
        """
        holidays, items = self._parse_arguments(args, instance_name=instance_name)

        arg = items[0]
        if isinstance(arg, int):  # A holiday name check for a specific year.
            holiday_years = {dt.year for dt in holidays.get_named(name, lookup="exact")}
            self.assertTrue(set(items).issubset(holiday_years), name)
        elif isinstance(arg, date) or parse(arg):  # Exact date check.
            for dt in items:
                self.assertIn(name, holidays.get_list(dt), dt)
        else:
            raise ValueError(f"The {arg} wasn't caught by `assertHolidayName()`")

    def assertHolidayName(self, name, *args):
        """Assert either a holiday with a specific name exists or
        each holiday name matches an expected one.
        """
        self._assertHolidayName(name, "holidays", *args)

    def assertNonObservedHolidayName(self, name, *args):
        """Assert either a non-observed holiday with a specific name exists or
        each non-observed holiday name matches an expected one.
        """
        self._assertHolidayName(name, "holidays_non_observed", *args)

    # Holidays.
    def _assertHolidays(self, instance_name, *args):
        """Helper: assert holidays exactly match expected holidays."""
        holidays, expected_holidays = self._parse_arguments(
            args, expand_items=False, instance_name=instance_name
        )
        self._verify_type(holidays)

        # Check one by one for descriptive error messages.
        for dt, name in expected_holidays:
            self.assertIn(dt, holidays)
            self.assertEqual(name, holidays.get(dt), dt)

        self.assertEqual(
            len(holidays),
            len(expected_holidays),
            set((dt.strftime("%Y-%m-%d"), name) for dt, name in holidays.items()).difference(
                (dt, name) for dt, name in expected_holidays
            ),
        )

    def assertHolidays(self, *args):
        """Assert holidays exactly match expected holidays."""
        self._assertHolidays("holidays", *args)

    def assertNonObservedHolidays(self, *args):
        """Assert non-observed holidays exactly match expected holidays."""
        self._assertHolidays("holidays_non_observed", *args)

    # No holiday.
    def _assertNoHoliday(self, instance_name, *args):
        """Helper: assert each date is not a holiday."""
        holidays, dates = self._parse_arguments(args, instance_name=instance_name)

        for dt in dates:
            self.assertNotIn(dt, holidays, dt)

    def assertNoHoliday(self, *args):
        """Assert each date is not a holiday."""
        self._assertNoHoliday("holidays", *args)

    def assertNoNonObservedHoliday(self, *args):
        """Assert each date is not a non-observed holiday."""
        self._assertNoHoliday("holidays_non_observed", *args)

    # No holiday name.
    def _assertNoHolidayName(self, name, instance_name, *args):
        """Helper: assert a holiday with a specific name doesn't exist."""
        holidays, items = self._parse_arguments(
            args, instance_name=instance_name, raise_on_empty=False
        )

        if len(items) == 0:  # A holiday name check.
            self.assertFalse(holidays.get_named(name, lookup="exact"), name)
            return None

        arg = items[0]
        if isinstance(arg, int):  # A holiday name check for a specific year.
            holiday_years = {dt.year for dt in holidays.get_named(name, lookup="exact")}
            self.assertEqual(0, len(holiday_years.intersection(items)), name)
        elif isinstance(arg, date) or parse(arg):  # Exact date check.
            for dt in items:
                self.assertNotIn(name, holidays.get_list(dt), dt)
        else:
            raise ValueError(f"The {arg} wasn't caught by `assertNoHolidayName()`")

    def assertNoHolidayName(self, name, *args):
        """Assert a holiday with a specific name doesn't exist."""
        self._assertNoHolidayName(name, "holidays", *args)

    def assertNoNonObservedHolidayName(self, name, *args):
        """Assert a non-observed holiday with a specific name doesn't exist."""
        self._assertNoHolidayName(name, "holidays_non_observed", *args)

    # No holidays.
    def _assertNoHolidays(self, instance_name, *args):
        """Helper: assert holidays dict is empty."""
        holidays, _ = self._parse_arguments(
            args, instance_name=instance_name, raise_on_empty=False
        )
        self._verify_type(holidays)

        self.assertFalse(holidays)
        self.assertEqual(0, len(holidays))

    def assertNoHolidays(self, *args):
        """Assert holidays dict is empty."""
        self._assertNoHolidays("holidays", *args)

    def assertNoNonObservedHolidays(self, *args):
        """Assert non-observed holidays dict is empty."""
        self._assertNoHolidays("holidays_non_observed", *args)

    def _assertLocalizedHolidays(self, localized_holidays, language=None):
        """Helper: assert localized holidays match expected names."""
        instance = self.test_class(
            language=language, categories=tuple(self.test_class.supported_categories)
        )

        # Populate holidays for an entire year.
        self.assertIn(localized_holidays[0][0], instance)

        actual_holidays = tuple(
            sorted((dt.strftime("%Y-%m-%d"), name) for dt, name in instance.items())
        )
        self.assertEqual(
            actual_holidays,
            localized_holidays,
            "Please make sure all holiday names are localized: " f"{actual_holidays}",
        )

    def assertLocalizedHolidays(self, *args):
        """Helper: assert localized holidays match expected names."""
        arg = args[0]
        is_string = isinstance(arg, str)

        language = arg if is_string else None
        localized_holidays = args[1:] if is_string else args

        if language:
            self.set_language(language)
        for language in (language, "invalid", ""):
            self._assertLocalizedHolidays(localized_holidays, language)


class SundayHolidays(TestCase):
    """Common class to test countries with Sundays as a holidays."""

    def assertSundays(self, cls):
        holidays = cls(years=1989, include_sundays=True)
        self.assertHoliday(
            holidays,
            "1989-12-31",
        )
        self.assertEqual(53, len([s for s in holidays if s.weekday() == SUN]))

        holidays = cls(years=2032, include_sundays=True)
        self.assertHoliday(
            holidays,
            "2032-01-04",
        )
        self.assertEqual(52, len([s for s in holidays if s.weekday() == SUN]))

        self.assertNoHolidays(cls(include_sundays=True))

        for sunday in (
            "1989-12-31",
            "2017-02-05",
            "2017-02-12",
            "2032-02-29",
        ):
            self.assertEqual(parse(sunday).weekday(), SUN)
            self.assertHoliday(holidays, sunday)

        for non_sunday in (
            "2001-05-16",
            "2001-05-18",
            "2016-12-27",
            "2016-12-28",
            "2017-02-06",
            "2017-02-07",
            "2017-02-08",
            "2017-02-09",
            "2017-02-10",
        ):
            self.assertNotEqual(parse(non_sunday).weekday(), SUN)
            self.assertNoHoliday(holidays, non_sunday)
