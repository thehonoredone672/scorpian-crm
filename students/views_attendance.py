from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class LiveAttendanceCheckInView(APIView):
    """
    Core API Controller for SRS Module 6 (Attendance Management).
    Handles loading student roll-calls for a batch and saving daily logs.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, session_id):
        """Fetches all students assigned to the batch linked to this session."""
        try:
            # 1. Find the session to know which batch we are marking attendance for
            session = db['sessions'].find_one({"_id": ObjectId(session_id)})
            if not session:
                return Response({"error": "Active session instance not found."}, status=status.HTTP_404_NOT_FOUND)

            # 2. Query students belonging to this branch and assigned to this batch
            query = {"branch_id": session.get("branch_id")}
            
            # If your student document maps to a batch_id, filter by it
            if "batch_id" in session:
                query["batch_id"] = session["batch_id"]

            students_cursor = db['students'].find(query)
            roll_call_list = []

            for student in students_cursor:
                # Check if attendance was already marked for this student in this session
                existing_log = db['attendance'].find_one({
                    "session_id": ObjectId(session_id),
                    "student_id": student["_id"]
                })

                roll_call_list.append({
                    "student_id": str(student["_id"]),
                    "name": f"{student.get('first_name')} {student.get('last_name')}",
                    "current_belt": student.get("current_belt", "WHITE"),
                    "status": existing_log.get("status", "NOT_MARKED") if existing_log else "NOT_MARKED"
                })

            return Response(roll_call_list, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to load roll-call: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, session_id):
        """Commits an attendance log entry for a specific student."""
        data = request.data
        student_id = data.get("student_id")
        attendance_status = data.get("status") # EXPECTS: "PRESENT", "ABSENT", or "LEAVE"

        if not student_id or not attendance_status:
            return Response({"error": "Missing parameter records: student_id and status required."}, status=status.HTTP_400_BAD_REQUEST)

        if attendance_status not in ["PRESENT", "ABSENT", "LEAVE"]:
            return Response({"error": "Invalid status value provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Upsert entry into the attendance logs collection
            db['attendance'].update_one(
                {
                    "session_id": ObjectId(session_id),
                    "student_id": ObjectId(student_id)
                },
                {
                    "$set": {
                        "status": attendance_status,
                        "date": datetime.date.today().isoformat(),
                        "timestamp": datetime.datetime.utcnow()
                    }
                },
                upsert=True
            )
            return Response({"message": "Attendance record committed successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Database write failure: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)