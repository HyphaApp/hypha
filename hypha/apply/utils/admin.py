from enum import Enum, auto
from typing import Dict, Literal

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
        related = [f"{form}_set__{field}" for form, field in self.related_models]
        return qs.prefetch_related(*related)

    def _get_icon_str(self, field: Literal["lab", "application", "round"]) -> str:
        """Get the icon for the specified field

        Args:
            field: only supports `lab`, `application` & `round`

        Returns:
            str: the correlated wagtail icon name
        """
        match field:
            case "lab":
                icon_name = AdminIcon.LAB
            case "application":
                icon_name = AdminIcon.FUND
            case "round":
                icon_name = AdminIcon.ROUND
            case "_":
                icon_name = None

        if not icon_name:
            return ""

        return f'<svg width="0.85rem" height="0.85rem" aria-hidden="true"><use href="#icon-{icon_name}"></use></svg> '

    def _get_used_by_html(self, values: Dict[str, str | int], field: str) -> str | None:
        """Get the HTML for an object in the "Used By" column.

        Attempts to insert a title, icon & edit URL if possible

        Args:
            values: a dict containing the keys of `<field>__id` & `<field>__title`.
            field: the field of the used object

        Returns:
            A string if anything was able to be extracted, otherwise `None`
        """
        icon_html = self._get_icon_str(field)
        if title := values.get(f"{field}__title"):
            if id := values.get(f"{field}__id"):
                edit_url = reverse("wagtailadmin_pages:edit", args=(id,))
                return f"<a href={edit_url}>{icon_html}{title}</a>"
            # Edge case but if the object ID is missing, provide the title & icon w/o edit link
            return f"{icon_html}{title}"

        return None

    def _list_related(
        self,
        obj,
        form: Literal[
            "applicationbasereviewform", "roundbasereviewform", "labbasereviewform"
        ],
        field: Literal["lab", "application", "round"],
    ) -> str:
        """Get an HTML string containing all related objects

        Args:
            obj: a form object (ie. `ReviewForm`, `ApplicationForm`, etc.)
            form: related form types to pull
            field: the type being pulled

        Returns:
            str: an HTML string of all related funds, labs & rounds containing icons/links if they could be extracted

        """
        related_values = getattr(obj, f"{form}_set").values(
            f"{field}__title", f"{field}__id"
        )
        # return a string of the joined "used by" objects
        return ", ".join(
            [
                html_str
                for value in related_values
                if (html_str := self._get_used_by_html(value, field))
            ]
        )

    def used_by(self, obj):
        rows = []
        for form, field in self.related_models:
            related = self._list_related(obj, form, field)
            if related:
                rows.append(related)
        return mark_safe(", ".join(rows))


class RelatedFormsMixin:
    """
    Provide columns for Application forms, Review forms, and Determination forms attached to the object.

    Using to show the related forms in funds, labs and rounds listing.
    """

    def application_forms(self, obj):
        def build_urls(application_forms):
            for application_form in application_forms:
                url = reverse(
                    "funds_applicationform_modeladmin_edit",
                    args=[application_form.form.id],
                )
                yield f'<a href="{url}">{application_form}</a>'

        urls = list(build_urls(obj.forms.all()))

        if not urls:
            return

        return mark_safe("<br />".join(urls))

    def review_forms(self, obj):
        def build_urls(review_forms):
            for review_form in review_forms:
                url = reverse(
                    "review_reviewform_modeladmin_edit", args=[review_form.form.id]
                )
                yield f'<a href="{url}">{review_form}</a>'

        urls = list(build_urls(obj.review_forms.all()))

        if not urls:
            return

        return mark_safe("<br />".join(urls))

    def determination_forms(self, obj):
        def build_urls(determination_forms):
            for determination_form in determination_forms:
                url = reverse(
                    "determinations_determinationform_modeladmin_edit",
                    args=[determination_form.form.id],
                )
                yield f'<a href="{url}">{determination_form}</a>'

        urls = list(build_urls(obj.determination_forms.all()))

        if not urls:
            return

        return mark_safe("<br />".join(urls))


class AdminIcon(Enum):
    """
    Enum used to keep Wagtail icons consistent across the admin interface

    Icon names pulled from https://docs.wagtail.org/en/stable/advanced_topics/icons.html#available-icons
    """

    ROUND = auto()
    SCREENING_STATUS = auto()
    SEALED_ROUND = auto()
    FUND = auto()
    REQUEST_FOR_PARTNERS = auto()
    LAB = auto()
    REVIEWER_ROLE = auto()
    APPLICATION_FORM = auto()
    APPLY = auto()
    DOCUMENT_CATEGORY = auto()
    CONTRACT_DOCUMENT_CATEGORY = auto()
    PROJECT_FORM = auto()
    PROJECT_SOW_FORM = auto()
    PROJECT_REPORT_FORM = auto()
    PROJECT = auto()
    REVIEW_FORM = auto()
    CATEGORY = auto()
    META_TERM = auto()
    DETERMINATION_FORM = auto()

    def __get_wagtail_icon(self) -> str:
        """
        Get the wagtail string for the specified icon
        """
        match self:
            case (
                self.APPLICATION_FORM
                | self.PROJECT_FORM
                | self.PROJECT_SOW_FORM
                | self.REVIEW_FORM
                | self.PROJECT_REPORT_FORM
                | self.DETERMINATION_FORM
            ):
                return "form"
            case self.FUND | self.LAB:
                return "doc-empty"
            case self.REQUEST_FOR_PARTNERS | self.REVIEWER_ROLE:
                return "group"
            case self.DOCUMENT_CATEGORY | self.CONTRACT_DOCUMENT_CATEGORY:
                return "doc-full"
            case self.SCREENING_STATUS | self.META_TERM:
                return "tag"
            case self.ROUND:
                return "repeat"
            case self.SEALED_ROUND:
                return "lock"
            case self.PROJECT:
                return "folder-open-1"
            case self.CATEGORY:
                return "list-ul"
            case self.APPLY:
                return "folder-inverse"

    def __str__(self) -> str:
        return self.__get_wagtail_icon()
