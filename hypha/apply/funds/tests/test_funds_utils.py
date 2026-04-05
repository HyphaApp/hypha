"""Tests for funds/utils.py (excluding get_copied_form_name which has test_utils.py)."""

from django.test import SimpleTestCase, TestCase

from ..utils import (
    get_export_polling_time,
    get_or_create_default_screening_statuses,
    get_statuses_as_params,
)


class TestGetExportPollingTime(SimpleTestCase):
    def test_small_count_returns_minimum(self):
        self.assertEqual(get_export_polling_time(0), 2)
        self.assertEqual(get_export_polling_time(1), 2)
        self.assertEqual(get_export_polling_time(100), 2)

    def test_large_count_returns_maximum(self):
        self.assertEqual(get_export_polling_time(10000), 45)
        self.assertEqual(get_export_polling_time(7000), 45)

    def test_medium_count_returns_interval(self):
        # 600 / 150 = 4
        result = get_export_polling_time(600)
        self.assertEqual(result, 4)
        self.assertGreater(result, 2)
        self.assertLess(result, 45)

    def test_boundary_at_min_interval(self):
        # 300 / 150 = 2 == min_interval; neither strict branch matches → falls to else → max
        result = get_export_polling_time(300)
        self.assertEqual(result, 45)

    def test_boundary_upper(self):
        # 6750 / 150 = 45 → max_interval == interval, returns max
        result = get_export_polling_time(6750)
        self.assertEqual(result, 45)

    def test_return_type_is_int(self):
        self.assertIsInstance(get_export_polling_time(500), int)


class TestGetStatusesAsParams(SimpleTestCase):
    def test_single_status(self):
        result = get_statuses_as_params(["received"])
        self.assertEqual(result, "?status=received&")

    def test_multiple_statuses(self):
        result = get_statuses_as_params(["received", "in-discussion"])
        self.assertIn("status=received", result)
        self.assertIn("status=in-discussion", result)
        self.assertTrue(result.startswith("?"))

    def test_empty_list(self):
        result = get_statuses_as_params([])
        self.assertEqual(result, "?")


class TestGetOrCreateDefaultScreeningStatuses(TestCase):
    def test_returns_none_for_empty_querysets(self):
        from ..models.screening import ScreeningStatus

        empty = ScreeningStatus.objects.none()
        result = get_or_create_default_screening_statuses(empty, empty)
        self.assertEqual(result, [None, None])

    def test_sets_first_yes_as_default_when_no_default_exists(self):
        from ..models.screening import ScreeningStatus

        status = ScreeningStatus.objects.create(
            title="UniquePass_NoDefault", yes=True, default=False
        )
        # Use pk-specific queryset to avoid interference with pre-existing statuses
        yes_qs = ScreeningStatus.objects.filter(pk=status.pk)
        no_qs = ScreeningStatus.objects.none()

        get_or_create_default_screening_statuses(yes_qs, no_qs)

        status.refresh_from_db()
        self.assertTrue(status.default)

    def test_sets_first_no_as_default_when_no_default_exists(self):
        from ..models.screening import ScreeningStatus

        status = ScreeningStatus.objects.create(
            title="UniqueFail_NoDefault", yes=False, default=False
        )
        yes_qs = ScreeningStatus.objects.none()
        no_qs = ScreeningStatus.objects.filter(pk=status.pk)

        get_or_create_default_screening_statuses(yes_qs, no_qs)

        status.refresh_from_db()
        self.assertTrue(status.default)

    def test_returns_existing_default_without_changing_it(self):
        from ..models.screening import ScreeningStatus

        default = ScreeningStatus.objects.create(
            title="UniqueDefaultPass", yes=True, default=True
        )
        other = ScreeningStatus.objects.create(
            title="UniqueOtherPass", yes=True, default=False
        )
        # Scope queryset to just our two objects
        yes_qs = ScreeningStatus.objects.filter(pk__in=[default.pk, other.pk])
        no_qs = ScreeningStatus.objects.none()

        result = get_or_create_default_screening_statuses(yes_qs, no_qs)

        self.assertEqual(result[0], default)
        other.refresh_from_db()
        self.assertFalse(other.default)
