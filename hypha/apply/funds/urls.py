from django.urls import include, path
from django.views.generic import RedirectView

from hypha.apply.projects import urls as projects_urls

from .views import (
    AwaitingReviewSubmissionsListView,
    ExportSubmissionsByRound,
    GroupingApplicationsListView,
    ReminderDeleteView,
    ReviewerLeaderboard,
    ReviewerLeaderboardDetail,
    RevisionCompareView,
    RevisionListView,
    RoundListView,
    StaffAssignments,
    SubmissionDeleteView,
    SubmissionDetailPDFView,
    SubmissionDetailSimplifiedView,
    SubmissionDetailView,
    SubmissionEditView,
    SubmissionListView,
    SubmissionPrivateMediaView,
    SubmissionResultView,
    SubmissionsByRound,
    SubmissionsByStatus,
    SubmissionSealedView,
    SubmissionStaffFlaggedView,
    SubmissionUserFlaggedView,
    submission_success,
)
from .views_beta import (
    bulk_archive_submissions,
    bulk_delete_submissions,
    bulk_update_submissions_status,
    submission_all_beta,
)
from .views_partials import (
    get_applications_status_counts,
    partial_reviews_card,
    partial_reviews_decisions,
    partial_submission_activities,
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
        path("all/", SubmissionListView.as_view(), name="list"),
        path(
            "statuses/",
            get_applications_status_counts,
            name="applications_status_counts",
        ),
        path("all-beta/", submission_all_beta, name="list-beta"),
        path("all-beta/bulk_archive/", bulk_archive_submissions, name="bulk-archive"),
        path("all-beta/bulk_delete/", bulk_delete_submissions, name="bulk-delete"),
        path(
            "all-beta/bulk_update_status/",
            bulk_update_submissions_status,
            name="bulk-update-status",
        ),
        path("all-beta/submenu/funds/", sub_menu_funds, name="submenu-funds"),
        path("all-beta/submenu/leads/", sub_menu_leads, name="submenu-leads"),
        path("all-beta/submenu/rounds/", sub_menu_rounds, name="submenu-rounds"),
        path(
            "all-beta/submenu/reviewers/", sub_menu_reviewers, name="submenu-reviewers"
        ),
        path(
            "all-beta/submenu/meta-terms/",
            sub_menu_meta_terms,
            name="submenu-meta-terms",
        ),
        path(
            "all-beta/submenu/bulk-update-status/",
            sub_menu_update_status,
            name="submenu-update-status",
        ),
        path(
            "all-beta/submenu/bulk-update-lead/",
            sub_menu_bulk_update_lead,
            name="submenu-bulk-update-lead",
        ),
        path(
            "all-beta/submenu/bulk-update-reviewers/",
            sub_menu_bulk_update_reviewers,
            name="submenu-bulk-update-reviewers",
        ),
        path(
            "all-beta/submenu/category-options/",
            sub_menu_category_options,
            name="submenu-category-options",
        ),
        path(
            "all-beta/partials/review_decisions/",
            partial_reviews_decisions,
            name="partial-reviews-decisions",
        ),
        path("summary/", GroupingApplicationsListView.as_view(), name="summary"),
        path("result/", SubmissionResultView.as_view(), name="result"),
        path(
            "flagged/",
            include(
                [
                    path("", SubmissionUserFlaggedView.as_view(), name="flagged"),
                    path(
                        "staff/",
                        SubmissionStaffFlaggedView.as_view(),
                        name="staff_flagged",
                    ),
                ]
            ),
        ),
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
            "awaiting_review/",
            AwaitingReviewSubmissionsListView.as_view(),
            name="awaiting_review",
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
                        "partial/activities/",
                        partial_submission_activities,
                        name="partial-activities",
                    ),
                    path(
                        "partial/reviews-card/",
                        partial_reviews_card,
                        name="partial-reviews-card",
                    ),
                    path("edit/", SubmissionEditView.as_view(), name="edit"),
                    path("sealed/", SubmissionSealedView.as_view(), name="sealed"),
                    path(
                        "simplified/",
                        SubmissionDetailSimplifiedView.as_view(),
                        name="simplified",
                    ),
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
        path("<slug:status>/", SubmissionsByStatus.as_view(), name="status"),
    ],
    "submissions",
)

rounds_urls = (
    [
        path("", RoundListView.as_view(), name="list"),
        path("<int:pk>/", SubmissionsByRound.as_view(), name="detail"),
        path("export/<int:pk>/", ExportSubmissionsByRound.as_view(), name="export"),
    ],
    "rounds",
)


urlpatterns = [
    path("submissions/", include(submission_urls)),
    path("rounds/", include(rounds_urls)),
    path("projects/", include(projects_urls)),
]
