import factory
import wagtail_factories

from .models import ApplyHomePage


class ApplyHomePageFactory(wagtail_factories.PageFactory):
    site = factory.RelatedFactory(
        wagtail_factories.SiteFactory,
        'root_page',
        is_default_site=True,
    )
    parent = None

    class Meta:
        model = ApplyHomePage

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        try:
            # We cant use "django_get_or_create" in meta as wagtail factories wont respect it
            return model_class.objects.get(slug=kwargs['slug'])
        except model_class.DoesNotExist:
            return super()._create(model_class, *args, **kwargs)
