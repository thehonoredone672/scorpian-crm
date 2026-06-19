from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class ExamSessionView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        if getattr(request.user, 'role', '') != 'SUPER_ADMIN':
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        sessions = list(db['exam_sessions'].find().sort("date", -1))
        for s in sessions: s['id'] = str(s.pop('_id'))
        return Response(sessions, status=status.HTTP_200_OK)

    def post(self, request):
        if getattr(request.user, 'role', '') != 'SUPER_ADMIN':
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        date = data.get('date')
        branch = data.get('branch_name', 'ALL BRANCHES').upper()
        promotions = data.get('promotions', []) # [{student_id, student_name, old_belt, new_belt}]

        promoted_count = len([p for p in promotions if p.get('new_belt')])
        if promoted_count == 0:
            return Response({"error": "No promotions selected."}, status=status.HTTP_400_BAD_REQUEST)

        session_doc = {
            "date": date,
            "branch_name": branch,
            "instructor_name": getattr(request.user, 'name', 'Admin'),
            "promoted_count": promoted_count,
            "created_at": datetime.datetime.utcnow()
        }
        res = db['exam_sessions'].insert_one(session_doc)
        session_id = res.inserted_id

        promo_docs = []
        for p in promotions:
            if p.get('new_belt'):
                # 1. Update the student's actual profile
                db.students.update_one(
                    {"_id": ObjectId(p['student_id'])},
                    {"$set": {"current_belt": p['new_belt'].strip().upper()}}
                )
                # 2. Log the promotion history
                promo_docs.append({
                    "session_id": str(session_id),
                    "student_id": str(p['student_id']),
                    "student_name": p.get('student_name'),
                    "old_belt": p.get('old_belt'),
                    "new_belt": p.get('new_belt'),
                    "date": date,
                    "branch_name": branch
                })
        
        if promo_docs: db['exam_promotions'].insert_many(promo_docs)
        return Response({"message": "Belt exam logged successfully!"}, status=status.HTTP_201_CREATED)

class ExamEligibleStudentsView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        sport = request.query_params.get('sport')
        query = {"status": "ACTIVE", "enrolled_sports": sport}
        
        students = list(db['students'].find(query, {"first_name": 1, "last_name": 1, "current_belt": 1, "branch_name": 1}))
        students.sort(key=lambda x: str(x.get('first_name', '')).lower())
        
        result = [{"id": str(s['_id']), "name": f"{s.get('first_name', '')} {s.get('last_name', '')}", "belt": s.get('current_belt', 'WHITE'), "branch": s.get('branch_name')} for s in students]
        return Response(result, status=status.HTTP_200_OK)

class ExamSessionDetailView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, session_id):
        records = list(db['exam_promotions'].find({"session_id": session_id}, {"_id": 0}))
        return Response(records, status=status.HTTP_200_OK)