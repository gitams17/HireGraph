from django.urls import path
from workflows.views import WorkflowStatusView

urlpatterns = [
    path("<str:thread_id>/status/", WorkflowStatusView.as_view(), name="workflow-status"),
]
