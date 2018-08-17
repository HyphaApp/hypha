from django.utils.html import mark_safe


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
        return mark_safe('<br>'.join(rows))
