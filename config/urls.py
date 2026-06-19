from django.urls import path, include
from sports.views_progression import ProgressionEngineView
from students.views_dashboard import UnifiedDashboardMetricsView
from students.views_enrollments import StudentEnrollmentView
from sports.views_scheduling import BatchSchedulingView
from finance.views import InvoiceCreatePaymentView
from students.views_export import EnterpriseDataExportView 
from accounts.views_instructors import InstructorManagementView
from students.views import StudentPromoteView
from django.urls import path
from students.views_attendance import AttendanceSessionView, AttendanceEligibleStudentsView, AttendanceSessionDetailView
from accounts.views_branches import BranchListView
from students.views_exams import ExamSessionView, ExamEligibleStudentsView, ExamSessionDetailView

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

    path('api/students/promote/', StudentPromoteView.as_view(), name='student_promote'),

    # New Class-Based Attendance Routes
    path('api/attendance/sessions/', AttendanceSessionView.as_view(), name='attendance_sessions'),
    path('api/attendance/eligible/', AttendanceEligibleStudentsView.as_view(), name='attendance_eligible'),
    path('api/attendance/sessions/<str:session_id>/', AttendanceSessionDetailView.as_view(), name='attendance_detail'),

    path('api/exams/sessions/', ExamSessionView.as_view(), name='exam_sessions'),
    path('api/exams/eligible/', ExamEligibleStudentsView.as_view(), name='exam_eligible'),
    path('api/exams/sessions/<str:session_id>/', ExamSessionDetailView.as_view(), name='exam_detail'),
]