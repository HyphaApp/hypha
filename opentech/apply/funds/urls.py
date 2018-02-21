from django.conf.urls import url

from .views import SubmissionSearchView, SubmissionDetailView, SubmissionListView, demo_workflow


urlpatterns = [
    url(r'^demo/(?P<wf_id>[1-2])/$', demo_workflow, name="workflow_demo"),
    url(r'^submissions/$', SubmissionListView.as_view(), name="submissions"),
    url(r'^submissions/(?P<pk>\d+)/$', SubmissionDetailView.as_view(), name="submission"),
    url(r'^search$', SubmissionSearchView.as_view(), name="search"),
]
