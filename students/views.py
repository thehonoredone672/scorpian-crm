from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import uuid

class StudentDirectoryView(APIView):
    """
    Core API Controller for SRS Module 4 (Student Management).
    Executes deep profile commits and multitenant branch visibility filtering.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches all active student profiles isolated by the user's operational branch context."""
        user = request.user
        query = {}

        # Enforce strict multi-tenant boundary compliance for staff
        if user.role in ['BRANCH_MANAGER', 'INSTRUCTOR'] and hasattr(user, 'branch_id'):
            query["branch_id"] = ObjectId(user.branch_id)

        try:
            students_cursor = db['students'].find(query)
            students_payload = []
            
            for student in students_cursor:
                students_payload.append({
                    "id": str(student.get('_id')),
                    "student_id": student.get('student_id', 'N/A'),
                    "first_name": student.get('first_name'),
                    "last_name": student.get('last_name'),
                    "dob": student.get('dob'),
                    "blood_group": student.get('blood_group'),
                    "phone": student.get('phone'),
                    "parent_name": student.get('parent_name'),
                    "style": student.get('style', 'General Martial Arts'),
                    "current_belt": student.get('current_belt', 'WHITE'),
                    "status": student.get('status', 'ACTIVE')
                })
            return Response(students_payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Database read failure: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Processes admissions registration and structures the data into the MongoDB collection."""
        user = request.user
        data = request.data

        # Enforce parameter strict compliance validation checking
        if not data.get('first_name') or not data.get('last_name') or not data.get('phone'):
            return Response({"error": "Missing mandatory field records: First name, Last name, and Phone are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Map flat input configurations into structured database documents matching SRS data criteria
        student_document = {
            "student_id": f"STU-{uuid.uuid4().hex[:6].upper()}", # Unique tracking identifier code
            "first_name": data.get('first_name').strip(),
            "last_name": data.get('last_name').strip(),
            "dob": data.get('dob', None),
            "age": None, # Handled dynamically by data pipelines later
            "gender": data.get('gender', 'UNSPECIFIED'),
            "blood_group": data.get('blood_group', 'Unknown'),
            "phone": data.get('phone').strip(),
            "parent_name": data.get('parent_name', 'Unknown'),
            "style": data.get('style', 'Karate').strip(),
            "current_belt": data.get('current_belt', 'WHITE').upper(),
            "status": "ACTIVE",
            "branch_id": ObjectId(user.branch_id) if hasattr(user, 'branch_id') else None,
            "belt_history": [] # Multi-record log array for Module 8 tracking extensions
        }

        try:
            result = db['students'].insert_one(student_document)
            return Response({
                "message": "Student profile admitted successfully into master registry system.",
                "id": str(result.inserted_id),
                "student_id": student_document["student_id"]
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Commit verification transaction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)