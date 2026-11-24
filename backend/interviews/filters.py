import django_filters
from django.db.models import Q

from .models import Interview, InterviewStatus, InterviewType


class InterviewFilter(django_filters.FilterSet):
    application_id = django_filters.UUIDFilter(field_name="application_id")
    candidate_id = django_filters.UUIDFilter(field_name="application__candidate_id")
    job_id = django_filters.UUIDFilter(field_name="application__job_id")
    status = django_filters.ChoiceFilter(choices=InterviewStatus.choices)
    interview_type = django_filters.ChoiceFilter(choices=InterviewType.choices)
    from_date = django_filters.IsoDateTimeFilter(field_name="scheduled_start", lookup_expr="gte")
    to_date = django_filters.IsoDateTimeFilter(field_name="scheduled_end", lookup_expr="lte")
    my_interviews = django_filters.BooleanFilter(method="filter_my_interviews")

    class Meta:
        model = Interview
        fields = [
            "application_id",
            "candidate_id",
            "job_id",
            "status",
            "interview_type",
            "from_date",
            "to_date",
            "my_interviews",
        ]

    def filter_my_interviews(self, queryset, name, value):
        if not value:
            return queryset
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(participants__user=user).distinct()
