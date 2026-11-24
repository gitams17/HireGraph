import django_filters
from .models import Candidate


class CandidateFilter(django_filters.FilterSet):
    organization = django_filters.UUIDFilter(field_name="organization_id")
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    company = django_filters.CharFilter(field_name="current_company", lookup_expr="icontains")
    skill = django_filters.CharFilter(method="filter_by_skill")

    class Meta:
        model = Candidate
        fields = ["organization", "location", "company", "skill"]

    def filter_by_skill(self, queryset, name, value):
        if not value:
            return queryset
        # skills is a JSONField list of strings; case-insensitive check
        return queryset.filter(skills__icontains=value)
