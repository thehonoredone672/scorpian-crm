# Location: students/urls.py

from django.urls import path
from .views import StudentDirectoryView
from students.views_export import EnterpriseDataExportView

urlpatterns = [
    # Combines with root namespace to route traffic directly to: /api/students/
    path('', StudentDirectoryView.as_view(), name='student-directory-root'),
    path('api/export/<str:target_module>/', EnterpriseDataExportView.as_view(), name='enterprise_data_exporter'),
]