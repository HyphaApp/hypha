import wagtail_factories

from .models import ApplyHomePage


class ApplySiteFactory(wagtail_factories.SiteFactory):
    class Meta:
        django_get_or_create = ('hostname',)


class ApplyHomePageFactory(wagtail_factories.PageFactory):
    title = "Apply Home"
    slug = 'apply'

    class Meta:
        model = ApplyHomePage

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        try:
            # We cant use "django_get_or_create" in meta as wagtail factories wont respect it
            return model_class.objects.get(slug=kwargs['slug'])
        except model_class.DoesNotExist:
            return super()._create(model_class, *args, **kwargs)
