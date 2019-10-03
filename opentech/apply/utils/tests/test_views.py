from django.test import TestCase
from django.views.generic import UpdateView

from opentech.apply.utils.views import DelegatedViewMixin


class PatchedUpdateView(UpdateView):
    def get_object(self):
        return 1


class DelegatedView(DelegatedViewMixin, PatchedUpdateView):
    model = int  # pretend int is a model for the isinstance check

    def get_parent_kwargs(self):
        return {'instance': 3}


class TestDelegatedViewMixin(TestCase):
    def test_parent_access_if_no_object(self):
        self.assertEqual(DelegatedView().get_object(), 3)

    def test__access_if_no_object(self):
        view = DelegatedView()
        view.object = 3
        self.assertNotEqual(view.get_object(), 3)
        self.assertEqual(view.get_object(), 1)
