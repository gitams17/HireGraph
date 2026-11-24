import django_filters
from .models import Application, ApplicationStage


class ApplicationFilter(django_filters.FilterSet):
    organization = django_filters.UUIDFilter(field_name="organization_id")
    job = django_filters.UUIDFilter(field_name="job_id")
    candidate = django_filters.UUIDFilter(field_name="candidate_id")
    stage = django_filters.ChoiceFilter(choices=ApplicationStage.choices)

    class Meta:
        model = Application
        fields = ["organization", "job", "candidate", "stage"]
