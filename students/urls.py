# Location: students/urls.py

from django.urls import path
from .views_enrollments import StudentEnrollmentView
from .views import StudentDirectoryView
from .views_export import EnterpriseDataExportView  # Import your export engine view
from .views_history import StudentHistoryView

urlpatterns = [
    # Resolves: /api/students/
    path('', StudentDirectoryView.as_view(), name='student_directory'),
    path('export/', EnterpriseDataExportView.as_view(), {'target_module': 'students'}, name='export_students_data'),
    path('<str:student_id>/history/', StudentHistoryView.as_view(), name='student_history'),
    ]