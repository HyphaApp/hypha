from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView

from hypha.apply.projects import urls as projects_urls

from .views import (
    CreateProjectView,
    GroupingApplicationsListView,
    ProgressSubmissionView,
    ReminderCreateView,
    ReminderDeleteView,
    ReviewerLeaderboard,
    ReviewerLeaderboardDetail,
    RevisionCompareView,
    RevisionListView,
    RoundListView,
    StaffAssignments,
    SubmissionDeleteView,
    SubmissionDetailPDFView,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionPrivateMediaView,
    SubmissionResultView,
    SubmissionSealedView,
    TranslateSubmissionView,
    UpdateLeadView,
    UpdateMetaTermsView,
    UpdatePartnersView,
    UpdateReviewersView,
    htmx_archive_unarchive_submission,
    reminder_list,
    submission_success,
)
from .views_all import (
    bulk_archive_submissions,
    bulk_delete_submissions,
    bulk_update_submissions_status,
    submissions_all,
)
from .views_partials import (
    get_applications_status_counts,
    partial_meta_terms_card,
    partial_reviews_card,
    partial_reviews_decisions,
    partial_screening_card,
    partial_submission_activities,
    partial_submission_answers,
    partial_submission_lead,
    partial_translate_answers,
    sub_menu_bulk_update_lead,
    sub_menu_bulk_update_reviewers,
    sub_menu_category_options,
    sub_menu_funds,
    sub_menu_leads,
    sub_menu_meta_terms,
    sub_menu_reviewers,
    sub_menu_rounds,
    sub_menu_update_status,
)

revision_urls = (
    [
        path("", RevisionListView.as_view(), name="list"),
        path(
            "compare/<int:to>/<int:from>/",
            RevisionCompareView.as_view(),
            name="compare",
        ),
    ],
    "revisions",
)

reminders_urls = (
    [
        path("<int:pk>/delete/", ReminderDeleteView.as_view(), name="delete"),
    ],
    "reminders",
)


app_name = "funds"

submission_urls = (
    [
        path(
            "",
            RedirectView.as_view(pattern_name="funds:submissions:list"),
            name="overview",
        ),
        path("success/<int:pk>/", submission_success, name="success"),
        path("all/", submissions_all, name="list"),
        path(
            "statuses/",
            get_applications_status_counts,
            name="applications_status_counts",
        ),
        path("all/bulk_archive/", bulk_archive_submissions, name="bulk-archive"),
        path("all/bulk_delete/", bulk_delete_submissions, name="bulk-delete"),
        path(
            "all/bulk_update_status/",
            bulk_update_submissions_status,
            name="bulk-update-status",
        ),
        path("all/submenu/funds/", sub_menu_funds, name="submenu-funds"),
        path("all/submenu/leads/", sub_menu_leads, name="submenu-leads"),
        path("all/submenu/rounds/", sub_menu_rounds, name="submenu-rounds"),
        path("all/submenu/reviewers/", sub_menu_reviewers, name="submenu-reviewers"),
        path(
            "all/submenu/meta-terms/",
            sub_menu_meta_terms,
            name="submenu-meta-terms",
        ),
        path(
            "all/submenu/bulk-update-status/",
            sub_menu_update_status,
            name="submenu-update-status",
        ),
        path(
            "all/submenu/bulk-update-lead/",
            sub_menu_bulk_update_lead,
            name="submenu-bulk-update-lead",
        ),
        path(
            "all/submenu/bulk-update-reviewers/",
            sub_menu_bulk_update_reviewers,
            name="submenu-bulk-update-reviewers",
        ),
        path(
            "all/submenu/category-options/",
            sub_menu_category_options,
            name="submenu-category-options",
        ),
        path(
            "all/partials/review_decisions/",
            partial_reviews_decisions,
            name="partial-reviews-decisions",
        ),
        path("summary/", GroupingApplicationsListView.as_view(), name="summary"),
        path("result/", SubmissionResultView.as_view(), name="result"),
        path(
            "reviews/",
            include(
                [
                    path(
                        "", ReviewerLeaderboard.as_view(), name="reviewer_leaderboard"
                    ),
                    path(
                        "<int:pk>/",
                        ReviewerLeaderboardDetail.as_view(),
                        name="reviewer_leaderboard_detail",
                    ),
                ]
            ),
        ),
        path(
            "assignments/",
            include(
                [
                    path(
                        "staff/", StaffAssignments.as_view(), name="staff_assignments"
                    ),
                ]
            ),
        ),
        path(
            "<int:pk>/",
            include(
                [
                    path("", SubmissionDetailView.as_view(), name="detail"),
                    path(
                        "partial/lead/",
                        partial_submission_lead,
                        name="partial-get-lead",
                    ),
                    path(
                        "partial/activities/",
                        partial_submission_activities,
                        name="partial-activities",
                    ),
                    path("lead/update/", UpdateLeadView.as_view(), name="lead_update"),
                    path("archive/", htmx_archive_unarchive_submission, name="archive"),
                    path(
                        "partial/screening-card/",
                        partial_screening_card,
                        name="partial-screening-card",
                    ),
                    path(
                        "partial/meta-terms-card/",
                        partial_meta_terms_card,
                        name="partial-meta-terms-card",
                    ),
                    path(
                        "partial/translate/answers",
                        partial_translate_answers,
                        name="partial-translate-answers",
                    ),
                    path(
                        "project/create/",
                        CreateProjectView.as_view(),
                        name="create_project",
                    ),
                    path(
                        "partial/reminder-card/",
                        reminder_list,
                        name="partial-reminder-card",
                    ),
                    path(
                        "reminder/create/",
                        ReminderCreateView.as_view(),
                        name="create_reminder",
                    ),
                    path(
                        "translate/",
                        TranslateSubmissionView.as_view(),
                        name="translate",
                    ),
                    path(
                        "progress/", ProgressSubmissionView.as_view(), name="progress"
                    ),
                    path(
                        "reviewers/update/",
                        UpdateReviewersView.as_view(),
                        name="reviewers_update",
                    ),
                    path(
                        "partners/update/",
                        UpdatePartnersView.as_view(),
                        name="partners_update",
                    ),
                    path(
                        "metaterms/update/",
                        UpdateMetaTermsView.as_view(),
                        name="metaterms_update",
                    ),
                    path(
                        "partial/reviews-card/",
                        partial_reviews_card,
                        name="partial-reviews-card",
                    ),
                    path(
                        "partial/answers/",
                        partial_submission_answers,
                        name="partial-answers",
                    ),
                    path("edit/", SubmissionEditView.as_view(), name="edit"),
                    path("sealed/", SubmissionSealedView.as_view(), name="sealed"),
                    path(
                        "download/", SubmissionDetailPDFView.as_view(), name="download"
                    ),
                    path("delete/", SubmissionDeleteView.as_view(), name="delete"),
                    path(
                        "documents/<uuid:field_id>/<str:file_name>",
                        SubmissionPrivateMediaView.as_view(),
                        name="serve_private_media",
                    ),
                ]
            ),
        ),
        path(
            "<int:submission_pk>/",
            include(
                [
                    path("", include("hypha.apply.review.urls", namespace="reviews")),
                    path("revisions/", include(revision_urls, namespace="revisions")),
                    path("reminders/", include(reminders_urls, namespace="reminders")),
                ]
            ),
        ),
        path(
            "", include("hypha.apply.determinations.urls", namespace="determinations")
        ),
        path("", include("hypha.apply.flags.urls", namespace="flags")),
    ],
    "submissions",
)

rounds_urls = (
    [
        path("", RoundListView.as_view(), name="list"),
    ],
    "rounds",
)

urlpatterns = [
    path("submissions/", include(submission_urls)),
    path("rounds/", include(rounds_urls)),
]

if settings.PROJECTS_ENABLED:
    urlpatterns += [
        path("projects/", include(projects_urls)),
    ]
