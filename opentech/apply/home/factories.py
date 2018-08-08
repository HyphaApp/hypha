import factory
import wagtail_factories

from .models import ApplyHomePage


class ApplyHomePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = ApplyHomePage

    @factory.post_generation
    def site(self, create, extracted_site, **site_kwargs):
        if create:
            wagtail_factories.SiteFactory(root_page=self, is_default_site=True)
