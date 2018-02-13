from django.conf.urls import url

from .views import SubmissionDetailView, demo_workflow


urlpatterns = [
    url(r'^demo/(?P<wf_id>[1-2])/$', demo_workflow, name="workflow_demo"),
    url(r'^submission/(?P<pk>\d+)/$', SubmissionDetailView.as_view(), name="submission"),
]
