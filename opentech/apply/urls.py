from django.conf.urls import url

from .views import demo_workflow

urlpatterns = [
    url(r'^demo/(?P<wf_id>[1-2])/$', demo_workflow, name="workflow_demo")
]
