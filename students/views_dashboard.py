from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class UnifiedDashboardMetricsView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        user = request.user
        today_date = datetime.date.today().isoformat()

        try:
            # 1. Resolve exact Profile Name and Role
            user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
            user_record = None
            
            if user_id:
                try:
                    user_record = db.users.find_one({"_id": ObjectId(str(user_id))})
                except Exception:
                    pass

            display_name = "Authorized User"
            if user_record:
                display_name = user_record.get("name", user_record.get("email", "Authorized User"))
            else:
                display_name = getattr(user, 'name', None) or (user.dict.get('name') if hasattr(user, 'dict') else "Authorized User")

            user_role = getattr(user, 'role', 'INSTRUCTOR')

            # 2. Pull raw database snapshots
            all_students = list(db['students'].find({}))
            all_attendance = list(db['attendance'].find({"date": today_date}))
            all_payments = list(db['payments'].find({}))

            # STRICT BRANCH FILTERING: Only show branches that have actual students or staff assigned.
            # This completely ignores empty dummy branches.
            active_student_branches = [str(s.get('branch_name')).strip().upper() for s in all_students if s.get('branch_name')]
            active_staff_branches = [str(u.get('branch_name')).strip().upper() for u in db.users.find({"role": "INSTRUCTOR"}) if u.get('branch_name')]
            
            branch_names = sorted(list(set(active_student_branches + active_staff_branches)))

            # Load sports directory pricing to map individual financial liabilities
            sports_list = list(db['sports'].find({}))
            sports_price_map = {
                str(sport.get('name', '')).strip().lower(): float(sport.get('monthly_fee', 0.00))
                for sport in sports_list
            }

            def compute_scope_data(filter_branch=None):
                scope_students = [
                    s for s in all_students 
                    if not filter_branch or str(s.get('branch_name', '')).strip().upper() == str(filter_branch).upper()
                ]
                scope_student_ids = {s['_id'] for s in scope_students}

                present_count = sum(1 for a in all_attendance if a.get('student_id') in scope_student_ids and a.get('status') == 'PRESENT')
                absent_count = sum(1 for a in all_attendance if a.get('student_id') in scope_student_ids and a.get('status') == 'ABSENT')

                # Calculate total monthly liability dynamically based on enrolled sports
                total_expected = 0.00
                for student in scope_students:
                    enrolled_programs = student.get('enrolled_sports', [])
                    if not isinstance(enrolled_programs, list):
                        enrolled_programs = [student.get('style', 'Karate')]
                    
                    student_liability = 0.00
                    for program in enrolled_programs:
                        program_clean = str(program).strip().lower()
                        student_liability += sports_price_map.get(program_clean, 0.00)
                    
                    total_expected += student_liability

                collected = sum(
                    float(p.get('amount', 0)) for p in all_payments 
                    if p.get('type') == 'CREDIT' and (not filter_branch or str(p.get('branch_name', '')).strip().upper() == str(filter_branch).upper())
                )
                
                pending = max(0.00, total_expected - collected)

                return {
                    "total_students": len(scope_students),
                    "present": present_count,
                    "absent": absent_count,
                    "collected": collected,
                    "pending": pending
                }

            # 3. Build Response Payloads
            if user_role == 'SUPER_ADMIN':
                global_stats = compute_scope_data(filter_branch=None)
                
                branch_grid = []
                for b_name in branch_names:
                    b_stats = compute_scope_data(b_name)
                    branch_grid.append({
                        "branch_name": b_name,
                        "present": b_stats["present"],
                        "absent": b_stats["absent"],
                        "collected": b_stats["collected"],
                        "pending": b_stats["pending"]
                    })

                return Response({
                    "role": "SUPER_ADMIN",
                    "email": display_name,
                    "summary": global_stats,
                    "branches": branch_grid
                }, status=status.HTTP_200_OK)

            else:
                instructor_branch = getattr(user, 'branch_name', 'COIMBATORE').upper()
                localized_stats = compute_scope_data(instructor_branch)

                return Response({
                    "role": "INSTRUCTOR",
                    "email": display_name,
                    "branch_name": instructor_branch,
                    "summary": localized_stats,
                    "branches": []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Dashboard runtime fault: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)