from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import translation

from hypha.apply.funds.blocks import LocalizedFloatField


class TestLocalizedFloatField(TestCase):
    def setUp(self):
        self.field = LocalizedFloatField()

    # --- Both separators present: last one is the decimal ---

    def test_dot_thousands_comma_decimal(self):
        """1.000,50 → 1000.5 (dot-thousands, comma-decimal)"""
        self.assertAlmostEqual(self.field.clean("1.000,50"), 1000.5)

    def test_comma_thousands_dot_decimal(self):
        """1,000.50 → 1000.5 (comma-thousands, dot-decimal)"""
        self.assertAlmostEqual(self.field.clean("1,000.50"), 1000.5)

    # --- Multiple identical separators: all thousands ---

    def test_dot_thousands_millions(self):
        """1.000.000 → 1000000 (dot-thousands)"""
        self.assertAlmostEqual(self.field.clean("1.000.000"), 1_000_000)

    def test_comma_thousands_millions(self):
        """1,000,000 → 1000000 (comma-thousands)"""
        self.assertAlmostEqual(self.field.clean("1,000,000"), 1_000_000)

    # --- Single separator: 3 digits after = thousands, 1-2 digits = decimal ---

    def test_dot_thousands(self):
        """10.000 → 10000 (dot-thousands)"""
        self.assertAlmostEqual(self.field.clean("10.000"), 10_000)

    def test_comma_thousands(self):
        """10,000 → 10000 (comma-thousands)"""
        self.assertAlmostEqual(self.field.clean("10,000"), 10_000)

    def test_dot_decimal(self):
        """10.50 → 10.5 (dot-decimal)"""
        self.assertAlmostEqual(self.field.clean("10.50"), 10.5)

    def test_comma_decimal(self):
        """10,50 → 10.5 (comma-decimal)"""
        self.assertAlmostEqual(self.field.clean("10,50"), 10.5)

    def test_comma_decimal_one_digit(self):
        """1,5 → 1.5 (comma-decimal)"""
        self.assertAlmostEqual(self.field.clean("1,5"), 1.5)

    def test_large_amount_comma_decimal(self):
        """10000,00 → 10000.0 (comma-decimal, no thousands separator)"""
        self.assertAlmostEqual(self.field.clean("10000,00"), 10_000.0)

    # --- Plain numbers and integer/float return type ---

    def test_plain_integer(self):
        self.assertEqual(self.field.clean("10000"), 10_000)
        self.assertIsInstance(self.field.clean("10000"), int)

    def test_whole_number_returns_int(self):
        """10000.00 and 10000,00 should be stored as 10000, not 10000.0"""
        self.assertIsInstance(self.field.clean("10000.00"), int)
        self.assertIsInstance(self.field.clean("10000,00"), int)

    def test_fractional_number_returns_float(self):
        """10000.50 should be stored as 10000.5, not 10000"""
        result = self.field.clean("10000.50")
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, 10000.5)

    def test_zero(self):
        self.assertEqual(self.field.clean("0"), 0)
        self.assertIsInstance(self.field.clean("0"), int)

    # --- prepare_value: display stored value in locale format ---

    def test_prepare_value_uses_locale_decimal_separator(self):
        """Stored float 10000.5 should display as "10000,5" in a comma-decimal locale."""
        with translation.override("sv"):
            self.assertEqual(self.field.prepare_value(10000.5), "10000,5")

    def test_prepare_value_integer_unchanged(self):
        """Stored int 10000 should display as 10000 (no decimal separator added)."""
        with translation.override("sv"):
            self.assertEqual(self.field.prepare_value(10000), 10000)

    def test_prepare_value_string_unchanged(self):
        """A string value (re-display after validation error) is not reformatted."""
        with translation.override("sv"):
            self.assertEqual(self.field.prepare_value("10000,5"), "10000,5")

    # --- Validation ---

    def test_negative_rejected_when_min_value_set(self):
        field = LocalizedFloatField(min_value=0)
        with self.assertRaises(ValidationError):
            field.clean("-1")
