import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from hypha.apply.users.decorators import (
    staff_required,
)

from ..models import ApplicationSubmission

if settings.APPLICATION_TRANSLATIONS_ENABLED:
    from hypha.apply.translate.forms import TranslateSubmissionForm
    from hypha.apply.translate.utils import (
        get_lang_name,
        get_language_choices_json,
        get_translation_params,
        translate_application_form_data,
    )


@method_decorator(staff_required, name="dispatch")
class TranslateSubmissionView(View):
    template = "funds/includes/translate_application_form.html"

    if settings.APPLICATION_TRANSLATIONS_ENABLED:

        def dispatch(self, request, *args, **kwargs):
            self.submission = get_object_or_404(
                ApplicationSubmission, id=kwargs.get("pk")
            )
            if not request.user.is_org_faculty:
                messages.warning(
                    self.request,
                    "User attempted to translate submission but is not org faculty",
                )
                return HttpResponseRedirect(self.submission.get_absolute_url())
            return super(TranslateSubmissionView, self).dispatch(
                request, *args, **kwargs
            )

        def get(self, *args, **kwargs):
            translate_form = TranslateSubmissionForm()
            return render(
                self.request,
                self.template,
                context={
                    "form": translate_form,
                    "value": _("Update"),
                    "object": self.submission,
                    "json_choices": get_language_choices_json(self.request),
                },
            )

        def post(self, request, *args, **kwargs):
            form = TranslateSubmissionForm(self.request.POST)

            if form.is_valid():
                FROM_LANG_KEY = "from_lang"
                TO_LANG_KEY = "to_lang"

                from_lang = form.cleaned_data[FROM_LANG_KEY]
                to_lang = form.cleaned_data[TO_LANG_KEY]

                return HttpResponse(
                    status=204,
                    headers={
                        "HX-Trigger": json.dumps(
                            {
                                "translateSubmission": {
                                    FROM_LANG_KEY: from_lang,
                                    TO_LANG_KEY: to_lang,
                                }
                            }
                        ),
                    },
                )

            return render(
                self.request,
                self.template,
                context={
                    "form": form,
                    "value": _("Update"),
                    "object": self.submission,
                    "json_choices": get_language_choices_json(self.request),
                },
                status=400,
            )
    else:

        def get(self, *args, **kwargs):
            raise Http404

        def post(self, *args, **kwargs):
            raise Http404


@login_required
def partial_translate_answers(request: HttpRequest, pk: int) -> HttpResponse:
    """Partial to translate submissions's answers

    Args:
        request: HttpRequest object
        pk: pk of the submission to translate

    """
    if not settings.APPLICATION_TRANSLATIONS_ENABLED:
        raise Http404

    submission = get_object_or_404(ApplicationSubmission, pk=pk)

    if not request.user.is_org_faculty or request.method != "GET":
        return HttpResponse(status=204)

    ctx = {"object": submission}

    # The existing params that were in the URL when the request was made
    prev_params = get_translation_params(request.headers.get("Hx-Current-Url", ""))
    # The requested params provided in the GET request
    params = get_translation_params(request=request)

    updated_url = submission.get_absolute_url()

    message = None

    if params and not params[0] == params[1] and not params == prev_params:
        from_lang, to_lang = params
        try:
            submission.form_data = translate_application_form_data(
                submission, from_lang, to_lang
            )

            if current_url := request.headers.get("Hx-Current-Url"):
                updated_params = QueryDict(urlparse(current_url).query, mutable=True)
                updated_params["fl"] = from_lang
                updated_params["tl"] = to_lang
                updated_url = f"{updated_url}?{updated_params.urlencode()}"

            to_lang_name = get_lang_name(to_lang)
            from_lang_name = get_lang_name(from_lang)

            message = _("Submission translated from {fl} to {tl}.").format(
                fl=from_lang_name, tl=to_lang_name
            )

            ctx.update(
                {
                    "object": submission,
                    "from_lang_name": from_lang_name,
                    "to_lang_name": to_lang_name,
                }
            )
        except ValueError:
            # TODO: WA Error/failed message type rather than success
            message = _("Submission translation failed. Contact your Administrator.")
            return HttpResponse(
                status=400,
                headers={"HX-Trigger": json.dumps({"showMessage": {message}})},
            )

    elif params == prev_params:
        message = _("Translation cleared.")

    response = render(request, "funds/includes/rendered_answers.html", ctx)

    trigger_dict = {}
    if title := submission.form_data.get("title"):
        trigger_dict.update(
            {
                "translatedSubmission": {
                    "appTitle": title,
                    "docTitle": submission.title_text_display,
                }
            }
        )

    if message:
        trigger_dict.update({"showMessage": message})

    if trigger_dict:
        response["HX-Trigger"] = json.dumps(trigger_dict)

    response["HX-Replace-Url"] = updated_url

    return response
