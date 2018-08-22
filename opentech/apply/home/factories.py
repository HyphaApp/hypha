import factory
import wagtail_factories

from .models import ApplyHomePage


class ApplyHomePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = ApplyHomePage

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        try:
            # We cant use "django_get_or_create" in meta as wagtail factories wont respect it
            return model_class.objects.get(slug=kwargs['slug'])
        except model_class.DoesNotExist:
            return super()._create(model_class, *args, **kwargs)

    @factory.post_generation
    def parent(self, create, extracted_parent, **parent_kwargs):
        if create and not self.get_parent():
            root = ApplyHomePage.get_first_root_node()
            root.add_child(instance=self)

    @factory.post_generation
    def site(self, create, extracted_site, **site_kwargs):
        if create:
            wagtail_factories.SiteFactory(root_page=self, is_default_site=True)
