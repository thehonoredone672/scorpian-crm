from django.contrib import admin
from django.urls import path, include

# --- Accounts & Branches ---
from accounts.views_branches import BranchListView
from accounts.views_instructors import InstructorManagementView

# --- Students & Dashboard ---
from students.views import StudentPromoteView
from students.views_dashboard import UnifiedDashboardMetricsView
from students.views_enrollments import StudentEnrollmentView
from students.views_export import EnterpriseDataExportView 

# --- Attendance & Exams ---
from students.views_attendance import AttendanceSessionView, AttendanceEligibleStudentsView, AttendanceSessionDetailView
from students.views_exams import ExamSessionView, ExamEligibleStudentsView, ExamSessionDetailView

# --- Sports ---
from sports.views_sports import SportsManagementView, SportRosterView
from sports.views_scheduling import BatchSchedulingView
from sports.views_progression import ProgressionEngineView

# --- Finance ---
from finance.views import FinanceLedgerView


urlpatterns = [
    path('admin/', admin.site.urls),

    # ==========================================
    # AUTH & ACCOUNTS
    # ==========================================
    path('api/auth/', include('accounts.urls')),
    path('api/branches/', BranchListView.as_view(), name='branch_list'),
    path('api/instructors/', InstructorManagementView.as_view(), name='instructor_management'),

    # ==========================================
    # DASHBOARD
    # ==========================================
    path('api/dashboard/metrics/', UnifiedDashboardMetricsView.as_view(), name='dashboard_metrics_engine'),

    # ==========================================
    # LEADS (CRM PIPELINE)
    # ==========================================
    path('api/', include('leads.urls')),

    # ==========================================
    # STUDENTS
    # ==========================================
    path('api/students/promote/', StudentPromoteView.as_view(), name='student_promote'),
    path('api/students/<str:student_id>/enroll/', StudentEnrollmentView.as_view(), name='student_enrollment'),
    path('api/students/', include('students.urls')), # Catch-all for remaining student routes

    # ==========================================
    # ATTENDANCE
    # ==========================================
    path('api/attendance/sessions/', AttendanceSessionView.as_view(), name='attendance_sessions'),
    path('api/attendance/eligible/', AttendanceEligibleStudentsView.as_view(), name='attendance_eligible'),
    path('api/attendance/sessions/<str:session_id>/', AttendanceSessionDetailView.as_view(), name='attendance_detail'),

    # ==========================================
    # EXAMS
    # ==========================================
    path('api/exams/sessions/', ExamSessionView.as_view(), name='exam_sessions'),
    path('api/exams/eligible/', ExamEligibleStudentsView.as_view(), name='exam_eligible'),
    path('api/exams/sessions/<str:session_id>/', ExamSessionDetailView.as_view(), name='exam_detail'),

    # ==========================================
    # SPORTS
    # ==========================================
    path('api/sports/scheduling/batches/', BatchSchedulingView.as_view(), name='batch_scheduling'),
    path('api/sports/progression/', ProgressionEngineView.as_view(), name='progression_engine'),
    path('api/sports/<str:sport_name>/roster/', SportRosterView.as_view(), name='sport_roster'),
    path('api/sports/', SportsManagementView.as_view(), name='sports_management_root'),
    path('api/sports/', include('sports.urls')), # Catch-all for remaining sports routes

    # ==========================================
    # FINANCE
    # ==========================================
    path('api/finance/ledger/', FinanceLedgerView.as_view(), name='finance_ledger'),
    path('api/finance/ledger/export/', EnterpriseDataExportView.as_view(), {'target_module': 'ledger'}, name='export_ledger_data'),
]