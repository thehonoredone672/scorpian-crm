from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class StudentDirectoryView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        user = request.user
        query = {}

        if user.role != 'SUPER_ADMIN':
            # Safe DB lookup for GET requests
            user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
            user_record = db.users.find_one({"_id": ObjectId(str(user_id))}) if user_id else None
            instructor_branch = user_record.get('branch_name', 'COIMBATORE').upper() if user_record else 'COIMBATORE'
            query["branch_name"] = instructor_branch

        try:
            students = []
            for s in db['students'].find(query):
                students.append({
                    "id": str(s["_id"]),
                    "first_name": s.get("first_name", ""),
                    "last_name": s.get("last_name", ""),
                    "phone": s.get("phone", ""),
                    "enrolled_sports": s.get("enrolled_sports", [s.get("style", "Karate")]), 
                    "current_belt": s.get("current_belt", "WHITE"),
                    "branch_name": str(s.get("branch_name", "UNKNOWN")).upper(),
                    "status": s.get("status", "ACTIVE")
                })
            return Response(students, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user = request.user
        data = request.data
        
        if user.role == 'SUPER_ADMIN':
            return Response({"error": "Super Admins cannot admit students directly. This action requires an assigned Instructor node."}, status=status.HTTP_403_FORBIDDEN)

        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        
        if not first_name or not phone:
            return Response({"error": "Required tracking fields missing."}, status=status.HTTP_400_BAD_REQUEST)

        # THE FIX: Direct Database Lookup for Instructor Branch
        user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
        user_record = db.users.find_one({"_id": ObjectId(str(user_id))}) if user_id else None
        
        instructor_branch = None
        if user_record and user_record.get('branch_name'):
            instructor_branch = user_record.get('branch_name').strip().upper()

        if not instructor_branch:
            # Fallback to prevent hard crash if data is totally corrupted
            instructor_branch = "COIMBATORE"

        duplicate_check = db['students'].find_one({"first_name": first_name, "last_name": last_name, "phone": phone})
        if duplicate_check:
            return Response({"error": "Student profile already exists."}, status=status.HTTP_409_CONFLICT)

        # Handle UI Checkbox Arrays cleanly
        sports_input = data.get("style", ["Karate"])
        if isinstance(sports_input, str):
            sports_array = [s.strip() for s in sports_input.split(',')]
        else:
            sports_array = sports_input

        new_student = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "enrolled_sports": sports_array,
            "style": ", ".join(sports_array),
            "current_belt": "WHITE",
            "branch_name": instructor_branch,
            "status": "ACTIVE",
            "created_at": datetime.datetime.utcnow()
        }

        db['students'].insert_one(new_student)
        return Response({"message": "Student admitted successfully."}, status=status.HTTP_201_CREATED)

    def put(self, request):
        user = request.user
        data = request.data
        student_id = data.get("student_id")

        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        sports_input = data.get("style", [])
        if isinstance(sports_input, str):
            sports_array = [s.strip() for s in sports_input.split(',')] if sports_input else []
        else:
            sports_array = sports_input

        update_fields = {
            "phone": data.get("phone"),
            "status": data.get("status", "ACTIVE"),
            "updated_at": datetime.datetime.utcnow()
        }
        
        if sports_array:
            update_fields["enrolled_sports"] = sports_array
            update_fields["style"] = ", ".join(sports_array)

        if user.role == 'SUPER_ADMIN' and data.get("branch_name"):
            update_fields["branch_name"] = data.get("branch_name").strip().upper()

        try:
            db['students'].update_one({"_id": ObjectId(student_id)}, {"$set": update_fields})
            return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)