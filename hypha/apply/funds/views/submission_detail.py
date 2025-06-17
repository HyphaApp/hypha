from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import (
    DetailView,
)
from django.views.generic.detail import SingleObjectMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.views import ActivityContextMixin
from hypha.apply.users.decorators import (
    staff_required,
)
from hypha.apply.utils.models import PDFPageSettings
from hypha.apply.utils.pdfs import draw_submission_content, make_pdf
from hypha.apply.utils.views import (
    ViewDispatcher,
)

from ..models import (
    ApplicationSubmission,
    ReviewerSettings,
)
from ..permissions import (
    can_alter_archived_submissions,
    get_archive_view_groups,
    has_permission,
)
from ..workflows import DRAFT_STATE

if settings.APPLICATION_TRANSLATIONS_ENABLED:
    from hypha.apply.translate.utils import (
        get_lang_name,
        get_translation_params,
        translate_application_form_data,
    )


class AdminSubmissionDetailView(ActivityContextMixin, DetailView):
    template_name_suffix = "_admin_detail"
    model = ApplicationSubmission

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        if submission.status == DRAFT_STATE and not submission.can_view_draft(
            request.user
        ):
            raise Http404
        permission, _ = has_permission(
            "submission_view", request.user, object=submission, raise_exception=True
        )
        redirect = SubmissionSealedView.should_redirect(request, submission)
        return redirect or super().dispatch(request, *args, **kwargs)

    if settings.APPLICATION_TRANSLATIONS_ENABLED:

        def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
            self.object = self.get_object()

            extra_context = {}

            # Check for language params - if they exist and are valid then update the context
            if lang_params := get_translation_params(request=request):
                from_lang, to_lang = lang_params
                try:
                    self.object.form_data = translate_application_form_data(
                        self.object, from_lang, to_lang
                    )
                    extra_context.update(
                        {
                            "from_lang_name": get_lang_name(from_lang),
                            "to_lang_name": get_lang_name(to_lang),
                        }
                    )
                except ValueError:
                    # Language package isn't valid or installed, redirect to the submission w/o params
                    return redirect(self.object.get_absolute_url())

            context = self.get_context_data(object=self.object, **extra_context)
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        other_submissions = (
            self.model.objects.filter(user=self.object.user)
            .current()
            .exclude(id=self.object.id)
            .order_by("-submit_time")
        )
        if self.object.next:
            other_submissions = other_submissions.exclude(id=self.object.next.id)

        return super().get_context_data(
            other_submissions=other_submissions,
            archive_access_groups=get_archive_view_groups(),
            can_archive=can_alter_archived_submissions(self.request.user),
            **kwargs,
        )


class ReviewerSubmissionDetailView(ActivityContextMixin, DetailView):
    template_name_suffix = "_reviewer_detail"
    model = ApplicationSubmission

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers may sometimes be applicants as well.
        # or if requesting user is a co-applicant to application, return the Applicant view.
        if (
            submission.user == request.user
            or submission.co_applicants.filter(user=request.user).exists()
        ):
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        if submission.status == DRAFT_STATE:
            raise Http404

        permission, _ = has_permission(
            "submission_view", request.user, object=submission, raise_exception=True
        )

        reviewer_settings = ReviewerSettings.for_request(request)
        if reviewer_settings.use_settings:
            queryset = ApplicationSubmission.objects.for_reviewer_settings(
                request.user, reviewer_settings
            )
            # Reviewer can't view submission which is not listed in ReviewerSubmissionsTable
            if not queryset.filter(id=submission.id).exists():
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class PartnerSubmissionDetailView(ActivityContextMixin, DetailView):
    model = ApplicationSubmission

    def get_object(self):
        return super().get_object().from_draft()

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        permission, _ = has_permission(
            "submission_view", request.user, object=submission, raise_exception=True
        )
        # If the requesting user submitted the application, return the Applicant view.
        # Partners may sometimes be applicants as well.
        # or if requesting user is a co-applicant to application, return the Applicant view.
        if (
            submission.user == request.user
            or submission.co_applicants.filter(user=request.user).exists()
        ):
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow partners in the submission they are added as partners
        partner_has_access = submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access:
            raise PermissionDenied
        if submission.status == DRAFT_STATE:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class CommunitySubmissionDetailView(ActivityContextMixin, DetailView):
    template_name_suffix = "_community_detail"
    model = ApplicationSubmission

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        permission, _ = has_permission(
            "submission_view", request.user, object=submission, raise_exception=True
        )
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers may sometimes be applicants as well.
        # or if requesting user is a co-applicant to application, return the Applicant view.
        if (
            submission.user == request.user
            or submission.co_applicants.filter(user=request.user).exists()
        ):
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow community reviewers in submission with a community review state.
        if not submission.community_review:
            raise PermissionDenied
        if submission.status == DRAFT_STATE:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class ApplicantSubmissionDetailView(ActivityContextMixin, DetailView):
    model = ApplicationSubmission

    def get_object(self):
        return super().get_object().from_draft()

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        permission, _ = has_permission(
            "submission_view", request.user, object=submission, raise_exception=True
        )
        # This view is only for applicants and co-applicants.
        if (
            submission.user != request.user
            and not submission.co_applicants.filter(user=request.user).exists()
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SubmissionDetailView(ViewDispatcher):
    admin_view = AdminSubmissionDetailView
    reviewer_view = ReviewerSubmissionDetailView
    partner_view = PartnerSubmissionDetailView
    community_view = CommunitySubmissionDetailView
    applicant_view = ApplicantSubmissionDetailView


@method_decorator(staff_required, "dispatch")
class SubmissionSealedView(DetailView):
    template_name = "funds/submission_sealed.html"
    model = ApplicationSubmission

    def get(self, request, *args, **kwargs):
        submission = self.get_object()
        if not self.round_is_sealed(submission):
            return self.redirect_detail(submission)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        submission = self.get_object()
        if self.can_view_sealed(request.user):
            self.peeked(submission)
        return self.redirect_detail(submission)

    def redirect_detail(self, submission):
        return HttpResponseRedirect(
            reverse_lazy("funds:submissions:detail", args=(submission.id,))
        )

    def peeked(self, submission):
        messenger(
            MESSAGES.OPENED_SEALED,
            request=self.request,
            user=self.request.user,
            source=submission,
        )
        self.request.session.setdefault("peeked", {})[str(submission.id)] = True
        # Dictionary updates do not trigger session saves. Force update
        self.request.session.modified = True

    def can_view_sealed(self, user):
        return user.is_superuser

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            can_view_sealed=self.can_view_sealed(self.request.user),
            **kwargs,
        )

    @classmethod
    def round_is_sealed(cls, submission):
        try:
            return submission.round.specific.is_sealed
        except AttributeError:
            # Its a lab - cant be sealed
            return False

    @classmethod
    def has_peeked(cls, request, submission):
        return str(submission.id) in request.session.get("peeked", {})

    @classmethod
    def should_redirect(cls, request, submission):
        if cls.round_is_sealed(submission) and not cls.has_peeked(request, submission):
            return HttpResponseRedirect(
                reverse_lazy("funds:submissions:sealed", args=(submission.id,))
            )


@method_decorator(staff_required, "dispatch")
class SubmissionDetailPDFView(SingleObjectMixin, View):
    model = ApplicationSubmission

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        pdf_page_settings = PDFPageSettings.load(request_or_site=request)
        content = draw_submission_content(self.object.output_text_answers())
        pdf = make_pdf(
            title=self.object.title,
            sections=[
                {
                    "content": content,
                    "title": "Submission",
                    "meta": [
                        self.object.stage,
                        self.object.page,
                        self.object.round,
                        f"Lead: {self.object.lead}",
                    ],
                },
            ],
            pagesize=pdf_page_settings.download_page_size,
        )
        return FileResponse(
            pdf,
            as_attachment=True,
            filename=self.object.title + ".pdf",
        )
