from django.urls import path, include
from sports.views_progression import ProgressionEngineView
from students.views_dashboard import UnifiedDashboardMetricsView
from students.views_enrollments import StudentEnrollmentView
from sports.views_scheduling import BatchSchedulingView
from students.views_attendance import LiveAttendanceCheckInView
from finance.views import InvoiceCreatePaymentView
from students.views_export import EnterpriseDataExportView 
from accounts.views_instructors import InstructorManagementView

from accounts.views_branches import BranchListView

urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('api/sports/', include('sports.urls')),
    path('api/branches/', BranchListView.as_view(), name='branch_list'),
    path('api/students/', include('students.urls')),
    
    # CONNECT MODULE 3: LEAD PIPELINE WITH THE MATCHING API PREFIX
    path('api/', include('leads.urls')),
    
    path('api/sports/scheduling/batches/', BatchSchedulingView.as_view(), name='batch_scheduling'),
    path('api/sports/<str:sport_id>/progression/', ProgressionEngineView.as_view(), name='progression_engine'),
    path('api/students/<str:student_id>/enroll/', StudentEnrollmentView.as_view(), name='student_enrollment'),
    path('api/sessions/<str:session_id>/checkin/', LiveAttendanceCheckInView.as_view(), name='live_attendance_checkin'),
    
    # Financial Ledger Routing Hook
    path('api/finance/ledger/', InvoiceCreatePaymentView.as_view(), name='financial_ledger'),
    # Location: config/urls.py (Your global root routing file)
    # Add this entry inside your main project urlpatterns array:

    path('api/finance/ledger/export/', EnterpriseDataExportView.as_view(), {'target_module': 'ledger'}, name='export_ledger_data'),
    # Location: config/urls.py
    # Ensure your progression line entry inside urlpatterns list points to the root path without parameters:

    path('api/sports/progression/', ProgressionEngineView.as_view(), name='progression_engine'),

    path('api/instructors/', InstructorManagementView.as_view(), name='instructor_management'),

    path('api/dashboard/metrics/', UnifiedDashboardMetricsView.as_view(), name='dashboard_metrics_engine'),
]