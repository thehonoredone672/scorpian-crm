from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
import datetime
from bson import ObjectId

def get_true_branch(user):
    branch = getattr(user, 'branch_name', None)
    if not branch and hasattr(user, 'dict'): branch = user.dict.get('branch_name')
    if not branch:
        user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
        if user_id:
            try:
                record = db.users.find_one({"_id": ObjectId(str(user_id))})
                if record: branch = record.get('branch_name')
            except: pass
    return branch.strip().upper() if branch else ""

class UnifiedDashboardMetricsView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        try:
            role = getattr(request.user, 'role', 'INSTRUCTOR')
            branch = get_true_branch(request.user)
            today = datetime.datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            month_str = today.strftime("%Y-%m")
            past10th = today.day > 10

            # ---------------------------------------------------------
            # SUPER ADMIN LOGIC (Clean Global Overview + 3-Col Branches)
            # ---------------------------------------------------------
            if role == 'SUPER_ADMIN':
                students = list(db['students'].find())
                instructors = list(db['users'].find({"role": "INSTRUCTOR"}))
                today_sessions = list(db['attendance_sessions'].find({"date": today_str}))
                month_ledgers = list(db['finance_ledger'].find({"date_string": {"$regex": f"^{month_str}"}}))

                total_active = sum(1 for s in students if s.get('status') != 'INACTIVE')
                collected_month = sum(float(l.get('amount', 0)) for l in month_ledgers)
                pending_month = sum(float(s.get('outstanding_balance', 0)) for s in students if s.get('status') != 'INACTIVE')

                branches_dict = {}

                # 1. Pre-fill all explicit branches from the DB
                try:
                    for b in db['branches'].find():
                        b_name = b.get('name', 'UNKNOWN').upper()
                        branches_dict[b_name] = {"name": b_name, "instructors": [], "students": 0, "present": 0, "absent": 0, "collected": 0, "pending": 0, "alert_count": 0}
                except: pass

                # 2. Map Instructors to Branches
                for inst in instructors:
                    b_name = inst.get('branch_name', 'UNKNOWN').upper()
                    if b_name not in branches_dict:
                        branches_dict[b_name] = {"name": b_name, "instructors": [], "students": 0, "present": 0, "absent": 0, "collected": 0, "pending": 0, "alert_count": 0}
                    inst_name = inst.get('name', getattr(inst, 'first_name', 'Instructor'))
                    if inst_name not in branches_dict[b_name]["instructors"]:
                        branches_dict[b_name]["instructors"].append(inst_name)

                # 3. Map Students and Pending Dues
                for s in students:
                    b_name = s.get('branch_name', 'UNKNOWN').upper()
                    if b_name not in branches_dict:
                        branches_dict[b_name] = {"name": b_name, "instructors": [], "students": 0, "present": 0, "absent": 0, "collected": 0, "pending": 0, "alert_count": 0}
                    if s.get('status') != 'INACTIVE':
                        branches_dict[b_name]["students"] += 1
                        bal = float(s.get('outstanding_balance', 0))
                        branches_dict[b_name]["pending"] += bal
                        if bal > 0 and past10th:
                            branches_dict[b_name]["alert_count"] += 1

                # 4. Map Attendance
                for s in today_sessions:
                    b_name = s.get('branch_name', 'UNKNOWN').upper()
                    if b_name in branches_dict:
                        branches_dict[b_name]["present"] += s.get('present_count', 0)
                        branches_dict[b_name]["absent"] += s.get('absent_count', 0)

                # 5. Map Revenue
                for l in month_ledgers:
                    b_name = l.get('branch_name', 'UNKNOWN').upper()
                    if b_name in branches_dict:
                        branches_dict[b_name]["collected"] += float(l.get('amount', 0))

                # Format Instructor Names
                for b in branches_dict.values():
                    b['instructors'] = ", ".join(b['instructors']) if b['instructors'] else "Unassigned"

                # Sort branches alphabetically A-Z
                sorted_branches = sorted(list(branches_dict.values()), key=lambda x: x['name'])

                return Response({
                    "view_type": "ADMIN",
                    "metrics": {
                        "total_active": total_active,
                        "total_instructors": len(instructors),
                        "collected_month": collected_month,
                        "pending_month": pending_month,
                        "branches": sorted_branches
                    }
                }, status=status.HTTP_200_OK)

            # ---------------------------------------------------------
            # INSTRUCTOR LOGIC (Branch Specific + Charts)
            # ---------------------------------------------------------
            else:
                query = {'branch_name': branch} if branch else {}
                students = list(db['students'].find(query))
                
                active_count = 0
                pending_count = 0
                for s in students:
                    status_val = s.get('status', 'ACTIVE')
                    bal = float(s.get('outstanding_balance', 0))
                    if status_val != 'INACTIVE' and bal > 0 and past10th: status_val = 'PENDING'
                    if status_val == 'ACTIVE': active_count += 1
                    elif status_val == 'PENDING': pending_count += 1

                att_query = query.copy()
                att_query['date'] = {"$regex": f"^{month_str}"}
                sessions = list(db['attendance_sessions'].find(att_query))
                total_p = sum(s.get('present_count', 0) for s in sessions)
                total_a = sum(s.get('absent_count', 0) for s in sessions)
                att_rate = int((total_p / (total_p + total_a) * 100)) if (total_p + total_a) > 0 else 0

                fin_query = query.copy()
                fin_query['date_string'] = {"$regex": f"^{today.strftime('%Y')}"}
                transactions = list(db['finance_ledger'].find(fin_query))

                fees_by_month = [0] * 12
                for t in transactions:
                    date_str = t.get('date_string', '')
                    if len(date_str) >= 7: fees_by_month[int(date_str[5:7]) - 1] += float(t.get('amount', 0))

                students_by_month = [0] * 12
                cumulative = 0
                for i in range(12):
                    m_str = f"{today.strftime('%Y')}-{str(i+1).zfill(2)}"
                    cumulative += sum(1 for s in students if str(s.get('created_at', '')).startswith(m_str))
                    students_by_month[i] = cumulative
                if cumulative == 0 and len(students) > 0: students_by_month[today.month - 1] = len(students)

                return Response({
                    "view_type": "INSTRUCTOR",
                    "metrics": {
                        "total_students": len(students),
                        "active_students": active_count,
                        "pending_students": pending_count,
                        "attendance_rate": att_rate
                    },
                    "chart": {
                        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                        "fees": fees_by_month,
                        "students": students_by_month
                    }
                }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print("DASHBOARD CRASH:", traceback.format_exc())
            return Response({"error": "Dashboard crash. Check terminal."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)