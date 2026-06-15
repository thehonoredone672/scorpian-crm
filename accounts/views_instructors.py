from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import bcrypt
import datetime

class InstructorManagementView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        if request.user.role != 'SUPER_ADMIN':
            return Response({"error": "Unauthorized. Super Admin access required."}, status=status.HTTP_403_FORBIDDEN)
            
        instructors = []
        for staff in db.users.find({"role": "INSTRUCTOR"}):
            instructors.append({
                "id": str(staff["_id"]),
                "name": staff.get("name", ""),
                "email": staff.get("email", ""),
                "branch_name": staff.get("branch_name", "Main Branch"),
                "status": staff.get("status", "ACTIVE")
            })
        return Response(instructors, status=status.HTTP_200_OK)

    def post(self, request):
        """Creates a brand new instructor profile."""
        if request.user.role != 'SUPER_ADMIN':
            return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data
        
        # Hash the admin-assigned password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(data.get("password", "Scorpion123!").encode('utf-8'), salt).decode('utf-8')

        new_instructor = {
            "name": data.get("name"),
            "email": data.get("email"),
            "password": hashed_password,
            "role": "INSTRUCTOR",
            "branch_name": data.get("branch_name"),
            "status": "ACTIVE",
            "created_at": datetime.datetime.utcnow()
        }

        db.users.insert_one(new_instructor)
        return Response({"message": "Instructor deployed to branch."}, status=status.HTTP_201_CREATED)

    def put(self, request):
        """Updates an existing instructor profile."""
        if request.user.role != 'SUPER_ADMIN':
            return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        instructor_id = data.get("instructor_id")

        if not instructor_id:
            return Response({"error": "Instructor ID missing."}, status=status.HTTP_400_BAD_REQUEST)

        # Build update payload
        update_fields = {
            "name": data.get("name"),
            "email": data.get("email"),
            "branch_name": data.get("branch_name"),
        }

        # Only update the password if the Super Admin explicitly typed a new one
        if data.get("password"):
            salt = bcrypt.gensalt()
            update_fields["password"] = bcrypt.hashpw(data.get("password").encode('utf-8'), salt).decode('utf-8')

        try:
            db.users.update_one(
                {"_id": ObjectId(instructor_id), "role": "INSTRUCTOR"},
                {"$set": update_fields}
            )
            return Response({"message": "Instructor parameters updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Database fault: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)