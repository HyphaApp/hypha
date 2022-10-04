from django.urls import reverse
from django.utils.safestring import mark_safe


class ListRelatedMixin:
    """Provides a used_by column which can  be found by defining related models in the
    following format:

    related_models = [
        (<related_name>, <field_name>),
    ]

    e.g. This would be object.<related_name>_set.field
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        related = [f'{form}_set__{field}' for form, field in self.related_models]
        return qs.prefetch_related(*related)

    def _list_related(self, obj, form, field):
        return ', '.join(getattr(obj, f'{form}_set').values_list(f'{field}__title', flat=True))

    def used_by(self, obj):
        rows = list()
        for form, field in self.related_models:
            related = self._list_related(obj, form, field)
            if related:
                rows.append(related)
        return ', '.join(rows)


class RelatedFormsMixin:
    """
    Provide columns for Application forms, Review forms, and Determination forms attached to the object.

    Using to show the related forms in funds, labs and rounds listing.
    """

    def application_forms(self, obj):

        def build_urls(application_forms):
            for application_form in application_forms:
                url = reverse('funds_applicationform_modeladmin_edit', args=[application_form.form.id])
                yield f'<a href="{url}">{application_form}</a>'

        urls = list(build_urls(obj.forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))

    def review_forms(self, obj):
        def build_urls(review_forms):
            for review_form in review_forms:
                url = reverse('review_reviewform_modeladmin_edit', args=[review_form.form.id])
                yield f'<a href="{url}">{review_form}</a>'

        urls = list(build_urls(obj.review_forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))

    def determination_forms(self, obj):
        def build_urls(determination_forms):
            for determination_form in determination_forms:
                url = reverse('determinations_determinationform_modeladmin_edit', args=[determination_form.form.id])
                yield f'<a href="{url}">{determination_form}</a>'

        urls = list(build_urls(obj.determination_forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))
