from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class StudentListCreateView(APIView):
    """
    Core CRM engine for enrolling and managing academy students.
    Enforces Strict Tenant Isolation (Branch-Level Data Siloing).
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        user = request.user
        students_collection = db['students']
        
        # Base query to only fetch currently active students
        query = {"status": "ACTIVE"}

        # FIREWALL: Enforce Logical Data Isolation
        if user.role == 'SUPER_ADMIN':
            pass # Global access granted
        elif user.role == 'BRANCH_MANAGER':
            # Lock the query to their specific assigned franchise location
            query["branch_id"] = ObjectId(user.branch_id)
        else:
            return Response({"error": "Insufficient clearance to view student manifests."}, status=status.HTTP_403_FORBIDDEN)

        cursor = students_collection.find(query)
        
        student_list = []
        for student in cursor:
            student['_id'] = str(student['_id'])
            student['branch_id'] = str(student['branch_id'])
            student_list.append(student)
            
        return Response(student_list, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        
        # Determine the Branch ID context contextually based on who is making the request
        if user.role == 'SUPER_ADMIN':
            branch_id_str = data.get('branch_id')
            if not branch_id_str:
                return Response({"error": "Super Admins must explicitly specify a target branch_id in the payload."}, status=status.HTTP_400_BAD_REQUEST)
        elif user.role == 'BRANCH_MANAGER':
            # Auto-assign the student to the manager's branch. Never trust client input for this.
            branch_id_str = user.branch_id
        else:
            return Response({"error": "Unauthorized role for enrollment operations."}, status=status.HTTP_403_FORBIDDEN)

        try:
            branch_obj_id = ObjectId(branch_id_str)
        except Exception:
            return Response({"error": "Malformed Branch ID parameter."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate required data
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not first_name or not last_name:
            return Response({"error": "First and Last name are mandatory parameters."}, status=status.HTTP_400_BAD_REQUEST)

        new_student = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": data.get('email', ''),
            "phone": data.get('phone', ''),
            "branch_id": branch_obj_id,
            "status": "ACTIVE",
            "enrollment_date": datetime.datetime.now(datetime.timezone.utc),
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        result = db['students'].insert_one(new_student)
        
        return Response({
            "message": "Student profile successfully registered to branch.",
            "student_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)