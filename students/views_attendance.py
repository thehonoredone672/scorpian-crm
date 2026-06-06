from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class LiveAttendanceCheckInView(APIView):
    """
    Processes real-time class check-ins and evaluates promotion thresholds.
    """
    authentication_classes = [MongoJWTAuthentication]

    def post(self, request, session_id):
        user = request.user
        data = request.data
        student_id_str = data.get('student_id')
        attendance_status = data.get('status', 'PRESENT') # PRESENT, ABSENT, EXCUSED

        if not student_id_str:
            return Response({"error": "student_id parameter is required for check-in."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_obj_id = ObjectId(session_id)
            student_obj_id = ObjectId(student_id_str)
        except Exception:
            return Response({"error": "Invalid parameters: Malformed ObjectId string."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Fetch target session record
        session = db['sessions'].find_one({"_id": session_obj_id})
        if not session:
            return Response({"error": "Target class session instance not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Security Tenant Boundary Check
        if user.role == 'BRANCH_MANAGER' and str(session['branch_id']) != user.branch_id:
            return Response({"error": "Unauthorized: Target session belongs to a different branch silo."}, status=status.HTTP_403_FORBIDDEN)

        # 3. Guard against double-logging the same student for the same class
        db['sessions'].update_one(
            {"_id": session_obj_id},
            {"$pull": {"attendance_records": {"student_id": student_obj_id}}}
        )

        # 4. Inject the fresh check-in log record
        check_in_entry = {
            "student_id": student_obj_id,
            "status": attendance_status,
            "marked_by": ObjectId(user.id),
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }

        db['sessions'].update_one(
            {"_id": session_obj_id},
            {"$push": {"attendance_records": check_in_entry}}
        )

        # =========================================================================
        # PROMOTION LOGIC ENGINE (AUTOMATED EVALUATION CORNERSTONE)
        # =========================================================================
        sport_id = session['sport_id']
        branch_id = session['branch_id']

        # Fetch student's current enrollment record for this specific sport
        enrollment = db['enrollments'].find_one({"student_id": student_obj_id, "sport_id": sport_id})
        if not enrollment:
            return Response({"message": "Attendance tracked successfully. (No sport enrollment found for auto-promotion evaluation)."}, status=status.HTTP_200_OK)

        current_level_id = enrollment.get('current_level_id')
        current_level = db['progression_levels'].find_one({"_id": current_level_id}) if current_level_id else None

        if current_level:
            # Calculate metrics: total scheduled classes vs total classes attended by this student
            total_sessions = db['sessions'].count_documents({"batch_id": session['batch_id'], "status": "SCHEDULED"})
            attended_sessions = db['sessions'].count_documents({
                "batch_id": session['batch_id'],
                "attendance_records": {"$elemMatch": {"student_id": student_obj_id, "status": "PRESENT"}}
            })

            attendance_pct = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
            required_pct = current_level.get('requirements', {}).get('required_attendance_pct', 80)

            # Check if promotion requirements are met
            if attendance_pct >= required_pct:
                # Find the next progressive rank tier (level_order + 1)
                next_level = db['progression_levels'].find_one({
                    "sport_id": sport_id,
                    "level_order": current_level['level_order'] + 1
                })

                if next_level:
                    # Update enrollment document to reflect the auto-promotion tier swap
                    db['enrollments'].update_one(
                        {"_id": enrollment['_id']},
                        {
                            "$set": {
                                "current_level_id": next_level['_id'],
                                "last_promoted_at": datetime.datetime.now(datetime.timezone.utc)
                            }
                        }
                    )
                    return Response({
                        "message": "Attendance recorded. Core metrics analyzed.",
                        "attendance_percentage": f"{attendance_pct:.1f}%",
                        "status": f"🏆 CONGRATULATIONS! Student promoted to {next_level['level_name']}!"
                    }, status=status.HTTP_200_OK)

        return Response({
            "message": "Attendance tracked cleanly.",
            "attendance_percentage": f"{(attended_sessions / total_sessions * 100 if total_sessions > 0 else 0):.1f}%",
            "status": "Requirements for promotion pending."
        }, status=status.HTTP_200_OK)