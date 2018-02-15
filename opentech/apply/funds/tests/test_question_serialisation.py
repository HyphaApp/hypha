from django.test import TestCase

from .factories import ApplicationFormFactory, FundTypeFactory, RoundFactory, RoundFormFactory


class TestSerialisationQuestions(TestCase):
    def setUp(self):
        application_form = {
            'form_fields__0__email__': '',
            'form_fields__1__full_name__': '',
        }
        form = ApplicationFormFactory(**application_form)
        fund = FundTypeFactory()

        self.round_page = RoundFactory(parent=fund)
        RoundFormFactory(round=self.round_page, form=form)

    def test_convet_to_json(self):
        print(self.round_page.serialise_form())
