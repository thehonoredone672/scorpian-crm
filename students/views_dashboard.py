from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime
import math

class UnifiedDashboardMetricsView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        user = request.user
        current_datetime = datetime.datetime.utcnow()
        today_date = current_datetime.strftime("%Y-%m-%d")
        current_month_prefix = current_datetime.strftime("%Y-%m")
        
        # 10th DAY RULE CHECK for Delinquency
        is_past_collection_date = current_datetime.day > 10

        try:
            # 1. Resolve Exact Profile Name (Guarantee Fallback to fix undefined bug)
            user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
            user_record = db.users.find_one({"_id": ObjectId(str(user_id))}) if user_id else None
            
            display_name = "Authorized User"
            if user_record and user_record.get("name"):
                display_name = user_record.get("name")
            elif getattr(user, 'name', None):
                display_name = getattr(user, 'name')
            elif user_record and user_record.get("email"):
                display_name = user_record.get("email").split('@')[0]
                
            user_role = getattr(user, 'role', 'INSTRUCTOR')

            # 2. Pull Database Snapshots
            all_students = list(db['students'].find({"status": "ACTIVE"}))
            all_instructors = list(db.users.find({"role": "INSTRUCTOR"}))
            all_attendance = list(db['attendance'].find({"date": today_date}))
            all_payments = list(db['payments'].find({"type": "CREDIT"}))

            # 3. AGGRESSIVE BRANCH AGGREGATION (Fixes empty dashboard)
            db_branches = [str(b.get('name')).strip().upper() for b in db['branches'].find({}) if b.get('name')]
            staff_branches = [str(u.get('branch_name')).strip().upper() for u in all_instructors if u.get('branch_name')]
            student_branches = [str(s.get('branch_name')).strip().upper() for s in all_students if s.get('branch_name')]
            
            branch_names = sorted(list(set(db_branches + staff_branches + student_branches)))

            def compute_scope_data(filter_branch=None):
                scope_students = [s for s in all_students if not filter_branch or str(s.get('branch_name', '')).strip().upper() == str(filter_branch).upper()]
                scope_student_ids = {s['_id'] for s in scope_students}

                present_count = sum(1 for a in all_attendance if a.get('student_id') in scope_student_ids and a.get('status') == 'PRESENT')
                absent_count = sum(1 for a in all_attendance if a.get('student_id') in scope_student_ids and a.get('status') == 'ABSENT')

                collected_this_month = 0.00
                pending_this_month = 0.00
                total_pending_students = 0
                total_overdue_months = 0

                for student in scope_students:
                    # READ MANUAL FEE DIRECTLY FROM DB (No 2500 Fallback)
                    monthly_liability = float(student.get('custom_fee', 0.00))

                    student_payments = [p for p in all_payments if p.get('student_id') == str(student['_id']) or p.get('student_id') == student['_id']]
                    
                    student_paid_this_month = sum(float(p.get('amount', 0)) for p in student_payments if str(p.get('timestamp', p.get('date', ''))).startswith(current_month_prefix))
                    collected_this_month += student_paid_this_month
                    
                    # Only add to pending if the 10th of the month has passed
                    if is_past_collection_date:
                        pending_this_month += max(0.00, monthly_liability - student_paid_this_month)

                    # Historical Delinquency Tracking
                    enrollment_date = student.get('created_at', current_datetime)
                    if isinstance(enrollment_date, str):
                        try: enrollment_date = datetime.datetime.fromisoformat(enrollment_date.replace("Z", "+00:00"))
                        except: enrollment_date = current_datetime

                    months_enrolled = (current_datetime.year - enrollment_date.year) * 12 + (current_datetime.month - enrollment_date.month) + 1
                    
                    expected_months_to_pay = months_enrolled if is_past_collection_date else max(0, months_enrolled - 1)

                    if monthly_liability > 0:
                        total_historical_paid = sum(float(p.get('amount', 0)) for p in student_payments)
                        months_paid_for = math.floor(total_historical_paid / monthly_liability)
                        overdue_months = expected_months_to_pay - months_paid_for

                        if overdue_months >= 1:
                            total_pending_students += 1
                            total_overdue_months += overdue_months

                return {
                    "total_students": len(scope_students),
                    "present": present_count,
                    "absent": absent_count,
                    "collected": collected_this_month,
                    "pending": pending_this_month,
                    "pending_students_count": total_pending_students,
                    "total_pending_months": total_overdue_months
                }

            if user_role == 'SUPER_ADMIN':
                global_stats = compute_scope_data(filter_branch=None)
                global_stats["total_instructors"] = len(all_instructors)
                
                branch_grid = [{"branch_name": b, "stats": compute_scope_data(b)} for b in branch_names]

                return Response({
                    "role": "SUPER_ADMIN",
                    "name": display_name,
                    "summary": global_stats,
                    "branches": branch_grid
                }, status=status.HTTP_200_OK)

            else:
                instructor_branch = getattr(user, 'branch_name', '').upper()
                return Response({
                    "role": "INSTRUCTOR",
                    "name": display_name,
                    "summary": compute_scope_data(instructor_branch),
                    "branches": []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)