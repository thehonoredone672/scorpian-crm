from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class ProgressionEngineView(APIView):
    """
    Core API Controller for SRS Module 8 (Belt Examinations & Rank Progression).
    Evaluates promotional readiness and registers belt promotions inside MongoDB.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Scans student records to compile a multi-tenant list of rank eligibility."""
        user = request.user
        query = {"status": "ACTIVE"}

        # Enforce strict branch tenant security isolation boundaries
        if user.role in ['BRANCH_MANAGER', 'INSTRUCTOR'] and hasattr(user, 'branch_id'):
            query["branch_id"] = ObjectId(user.branch_id)

        try:
            students_cursor = db['students'].find(query)
            eligibility_manifest = []

            for student in students_cursor:
                student_id = student["_id"]
                
                # Dynamic Evaluation Parameter: Count total present sessions in the attendance collection
                present_count = db['attendance'].count_documents({
                    "student_id": student_id,
                    "status": "PRESENT"
                })

                # Business Rule Check: If they have attended at least 1 session, label them ELIGIBLE
                # (You can scale this number to 24+ sessions later based on your requirements)
                is_eligible = present_count >= 1 

                eligibility_manifest.append({
                    "id": str(student_id),
                    "name": f"{student.get('first_name')} {student.get('last_name')}",
                    "current_belt": student.get('current_belt', 'WHITE'),
                    "attendance_count": present_count,
                    "status": "ELIGIBLE" if is_eligible else "PENDING_HOURS"
                })

            return Response(eligibility_manifest, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to compute progression metrics: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Promotes a student to their next targeted belt tier and logs their martial arts rank history."""
        data = request.data
        student_id = data.get('student_id')
        next_belt = data.get('next_belt') # EXPECTS: "YELLOW", "GREEN", "BROWN", "BLACK"

        if not student_id or not next_belt:
            return Response({"error": "Missing promotion parameters: student_id and next_belt are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Atomic update transaction: update current belt status and push an immutable entry into the history log array
            result = db['students'].update_one(
                {"_id": ObjectId(student_id)},
                {
                    "$set": {
                        "current_belt": next_belt.upper()
                    },
                    "$push": {
                        "belt_history": {
                            "belt": next_belt.upper(),
                            "promoted_on": datetime.datetime.utcnow().isoformat(),
                            "authorized_by": str(request.user.id if hasattr(request.user, 'id') else 'SYSTEM')
                        }
                    }
                }
            )

            if result.matched_count == 0:
                return Response({"error": "Student record matching target ID not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": f"Promotion successful. Student rank upgraded to {next_belt} Belt."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to record rank transaction entry: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)