from django_filters import rest_framework as filters

from .models import JobRequisition


class JobRequisitionFilter(filters.FilterSet):
    status = filters.CharFilter(field_name="status", lookup_expr="exact")
    department = filters.CharFilter(field_name="department", lookup_expr="iexact")
    location = filters.CharFilter(field_name="location", lookup_expr="icontains")
    employment_type = filters.CharFilter(field_name="employment_type", lookup_expr="exact")

    class Meta:
        model = JobRequisition
        fields = ["status", "department", "location", "employment_type"]
