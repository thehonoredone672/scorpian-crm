from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class LiveAttendanceCheckInView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, session_id):
        user = request.user
        query = {"status": "ACTIVE"}
        
        # SUPER_ADMIN God Mode bypass: Only restrict if they are standard staff
        if user.role != 'SUPER_ADMIN' and hasattr(user, 'branch_id'):
            query["branch_id"] = ObjectId(user.branch_id)

        try:
            students_cursor = db['students'].find(query)
            roll_call_list = []
            today_date = datetime.date.today().isoformat()

            for student in students_cursor:
                # Check for attendance logged TODAY, ignoring strict session ID matching for now
                existing_log = db['attendance'].find_one({
                    "student_id": student["_id"],
                    "date": today_date
                })

                roll_call_list.append({
                    "student_id": str(student["_id"]),
                    "branch_id": str(student.get("branch_id")) if student.get("branch_id") else None,
                    "name": f"{student.get('first_name')} {student.get('last_name')}",
                    "current_belt": student.get("current_belt", "WHITE"),
                    "status": existing_log.get("status", "NOT_MARKED") if existing_log else "NOT_MARKED"
                })

            return Response(roll_call_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, session_id):
        data = request.data
        student_id = data.get("student_id")
        attendance_status = data.get("status")

        try:
            # Upsert entry tied strictly to the Student and TODAY'S date
            db['attendance'].update_one(
                {
                    "student_id": ObjectId(student_id),
                    "date": datetime.date.today().isoformat()
                },
                {
                    "$set": {
                        "status": attendance_status,
                        "timestamp": datetime.datetime.utcnow()
                    }
                },
                upsert=True
            )
            return Response({"message": "Locked."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)