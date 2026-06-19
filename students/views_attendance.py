from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

# --- AGGRESSIVE BRANCH RESOLUTION HELPER ---
def get_true_branch(user):
    branch = getattr(user, 'branch_name', None)
    if not branch and hasattr(user, 'dict'):
        branch = user.dict.get('branch_name')
    if not branch:
        user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
        if user_id:
            try:
                record = db.users.find_one({"_id": ObjectId(str(user_id))})
                if record: branch = record.get('branch_name')
            except: pass
    if not branch:
        email = getattr(user, 'email', None) or (user.dict.get('email') if hasattr(user, 'dict') else None)
        if email:
            record = db.users.find_one({"email": email})
            if record: branch = record.get('branch_name')
    return branch.strip().upper() if branch else ""
# -------------------------------------------

# --- AGGRESSIVE NAME RESOLUTION HELPER ---
def get_true_name(user):
    user_id = None
    email = None
    name = None
    
    # 1. Safely extract data whether 'user' is a dictionary OR a class object
    if isinstance(user, dict):
        user_id = user.get('_id') or user.get('id') or user.get('user_id')
        email = user.get('email')
        name = user.get('name')
    else:
        user_id = getattr(user, 'id', None) or getattr(user, '_id', None)
        email = getattr(user, 'email', None)
        name = getattr(user, 'name', None)
        
        # Check if custom auth attached a payload dictionary
        if not name and hasattr(user, 'dict') and isinstance(user.dict, dict):
            name = user.dict.get('name')
            user_id = user_id or user.dict.get('_id')
            email = email or user.dict.get('email')

    # 2. FORCE a direct MongoDB lookup using the exact "_id" or "email"
    from bson import ObjectId
    from database.mongodb_client import db
    
    if not name and user_id:
        try:
            record = db.users.find_one({"_id": ObjectId(str(user_id))})
            if record and record.get('name'):
                return str(record.get('name'))
        except: pass
        
    if not name and email:
        try:
            record = db.users.find_one({"email": email})
            if record and record.get('name'):
                return str(record.get('name'))
        except: pass
        
    # 3. Final Fallbacks
    if name: return str(name)
    if email: return str(email).split('@')[0]
    return "Instructor"
# -----------------------------------------

class AttendanceSessionView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        role = getattr(request.user, 'role', 'INSTRUCTOR')
        query = {}
        if role != 'SUPER_ADMIN':
            branch = get_true_branch(request.user)
            if branch: query['branch_name'] = branch

        sessions = list(db['attendance_sessions'].find(query).sort("date", -1))
        for s in sessions: s['id'] = str(s.pop('_id'))
        return Response(sessions, status=status.HTTP_200_OK)

    def post(self, request):
        if getattr(request.user, 'role', '') == 'SUPER_ADMIN':
            return Response({"error": "Admins cannot mark attendance."}, status=status.HTTP_403_FORBIDDEN)

        branch = get_true_branch(request.user)
        if not branch:
            return Response({"error": "Instructor branch assignment missing."}, status=status.HTTP_400_BAD_REQUEST)

        instructor_name = get_true_name(request.user)
        
        data = request.data
        sport = data.get('sport')
        date = data.get('date')
        time = data.get('time')
        records = data.get('records', [])

        present_count = sum(1 for r in records if r.get('status') == 'PRESENT')
        absent_count = sum(1 for r in records if r.get('status') == 'ABSENT')

        session_doc = {
            "branch_name": branch,
            "sport": sport,
            "date": date,
            "time": time,
            "instructor_name": instructor_name,
            "present_count": present_count,
            "absent_count": absent_count,
            "created_at": datetime.datetime.utcnow()
        }
        res = db['attendance_sessions'].insert_one(session_doc)
        session_id = res.inserted_id

        att_docs = []
        for r in records:
            att_docs.append({
                "session_id": str(session_id),
                "student_id": ObjectId(r['student_id']) if ObjectId.is_valid(r['student_id']) else r['student_id'],
                "student_name": r.get('student_name'),
                "date": date,
                "status": r.get('status'),
                "branch_name": branch
            })
        
        if att_docs: db['attendance'].insert_many(att_docs)
        return Response({"message": "Class attendance successfully recorded!"}, status=status.HTTP_201_CREATED)


class AttendanceEligibleStudentsView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        sport = request.query_params.get('sport')
        
        # Deploy aggressive branch lookup
        branch = get_true_branch(request.user)
        if not branch:
            return Response([], status=status.HTTP_200_OK)

        query = {"status": "ACTIVE", "branch_name": branch}
        if sport: query["enrolled_sports"] = sport

        students = list(db['students'].find(query, {"first_name": 1, "last_name": 1, "current_belt": 1}))
        
        # Alphabetical Sort
        students.sort(key=lambda x: str(x.get('first_name', '')).lower())
        
        result = [{"id": str(s['_id']), "name": f"{s.get('first_name', '')} {s.get('last_name', '')}", "belt": s.get('current_belt', 'WHITE')} for s in students]
        return Response(result, status=status.HTTP_200_OK)


class AttendanceSessionDetailView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, session_id):
        records = list(db['attendance'].find({"session_id": session_id}, {"_id": 0}))
        for r in records: r['student_id'] = str(r['student_id'])
        return Response(records, status=status.HTTP_200_OK)