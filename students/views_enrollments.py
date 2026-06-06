from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class StudentEnrollmentView(APIView):
    """
    Handles multi-sport registrations for individual students.
    Auto-assigns the foundational progression tier (e.g., White Belt) upon enrollment.
    """
    authentication_classes = [MongoJWTAuthentication]

    def post(self, request, student_id):
        user = request.user
        data = request.data
        sport_id_str = data.get('sport_id')

        if not sport_id_str:
            return Response({"error": "Target sport_id is required for enrollment."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_obj_id = ObjectId(student_id)
            sport_obj_id = ObjectId(sport_id_str)
        except Exception:
            return Response({"error": "Malformed ID parameters."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Tenant Security Firewall: Ensure the student exists AND belongs to the manager's branch
        student_query = {"_id": student_obj_id}
        if user.role == 'BRANCH_MANAGER':
            student_query["branch_id"] = ObjectId(user.branch_id)
            
        student = db['students'].find_one(student_query)
        if not student:
            return Response({"error": "Student not found or outside your branch jurisdiction."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Verify Sport Engine Exists
        if not db['sports'].find_one({"_id": sport_obj_id}):
            return Response({"error": "Target sport profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # 3. Prevent Duplicate Enrollments
        if db['enrollments'].find_one({"student_id": student_obj_id, "sport_id": sport_obj_id}):
            return Response({"error": "Student is already actively enrolled in this sport."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Intelligence Engine: Fetch the starting rank (Level Order 1) for this sport
        base_level = db['progression_levels'].find_one(
            {"sport_id": sport_obj_id, "level_order": 1}
        )
        base_level_id = base_level['_id'] if base_level else None

        # 5. Execute Enrollment Mapping
        new_enrollment = {
            "student_id": student_obj_id,
            "sport_id": sport_obj_id,
            "branch_id": student['branch_id'], # Inherit branch for analytics isolation
            "current_level_id": base_level_id,
            "status": "ACTIVE",
            "enrolled_date": datetime.datetime.now(datetime.timezone.utc)
        }

        result = db['enrollments'].insert_one(new_enrollment)

        return Response({
            "message": "Student successfully enrolled in new sport matrix.",
            "enrollment_id": str(result.inserted_id),
            "starting_level_assigned": bool(base_level_id)
        }, status=status.HTTP_201_CREATED)