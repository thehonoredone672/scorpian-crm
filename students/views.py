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
        role = getattr(request.user, 'role', 'INSTRUCTOR')
        query = {}
        
        if role != 'SUPER_ADMIN':
            # Aggressive lookup fallback for Instructors
            branch = getattr(request.user, 'branch_name', None) or (request.user.dict.get('branch_name') if hasattr(request.user, 'dict') else None)
            if not branch:
                user_id = getattr(request.user, 'id', None) or (request.user.dict.get('_id') if hasattr(request.user, 'dict') else None)
                if user_id:
                    user_record = db.users.find_one({"_id": ObjectId(str(user_id))})
                    if user_record: branch = user_record.get('branch_name')
            if branch:
                query['branch_name'] = branch.upper()

        students = list(db['students'].find(query))
        
        # Alphabetical sort by first name
        students.sort(key=lambda x: str(x.get('first_name', '')).lower())
        
        for s in students:
            s['id'] = str(s.pop('_id'))
            if 'created_at' in s: s['created_at'] = str(s['created_at'])
        return Response(students, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        
        if getattr(user, 'role', '') == 'SUPER_ADMIN' or request.data.get('role') == 'SUPER_ADMIN':
            return Response({"error": "Super Admins cannot admit students directly. Log in as an Instructor."}, status=status.HTTP_403_FORBIDDEN)

        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        
        try: custom_fee = float(data.get("custom_fee", 0.00))
        except ValueError: custom_fee = 0.00

        if not first_name or not phone:
            return Response({"error": "Required tracking fields missing."}, status=status.HTTP_400_BAD_REQUEST)

        # Aggressive Branch Resolution
        instructor_branch = getattr(user, 'branch_name', None)
        if not instructor_branch and hasattr(user, 'dict'):
            instructor_branch = user.dict.get('branch_name')

        if not instructor_branch:
            user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
            if user_id:
                try:
                    user_record = db.users.find_one({"_id": ObjectId(str(user_id))})
                    if user_record: instructor_branch = user_record.get('branch_name')
                except: pass

        if not instructor_branch:
            user_email = getattr(user, 'email', None) or (user.dict.get('email') if hasattr(user, 'dict') else None)
            if user_email:
                user_record = db.users.find_one({"email": user_email})
                if user_record: instructor_branch = user_record.get('branch_name')

        if not instructor_branch:
            return Response({"error": "System Alert: Instructor profile is corrupted or missing a branch assignment. Please check the Instructor Roster."}, status=status.HTTP_400_BAD_REQUEST)

        instructor_branch = instructor_branch.strip().upper()

        duplicate_check = db['students'].find_one({"first_name": first_name, "last_name": last_name, "phone": phone})
        if duplicate_check:
            return Response({"error": "Student profile already exists."}, status=status.HTTP_409_CONFLICT)

        sports_input = data.get("style", ["Karate"])
        sports_array = [s.strip() for s in sports_input.split(',')] if isinstance(sports_input, str) else sports_input

        new_student = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "enrolled_sports": sports_array,
            "custom_fee": custom_fee,
            "style": ", ".join(sports_array),
            "current_belt": "WHITE",
            "branch_name": instructor_branch,
            "status": "ACTIVE",
            "created_at": datetime.datetime.utcnow()
        }

        db['students'].insert_one(new_student)
        return Response({"message": "Student admitted successfully."}, status=status.HTTP_201_CREATED)

    def put(self, request):
        student_id = request.data.get("student_id")
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        update_fields = {}
        if "phone" in request.data: update_fields["phone"] = request.data.get("phone").strip()
        if "status" in request.data: update_fields["status"] = request.data.get("status").strip()
        
        try: 
            if "custom_fee" in request.data:
                update_fields["custom_fee"] = float(request.data.get("custom_fee", 0.00))
        except ValueError: pass

        if "style" in request.data:
            sports_input = request.data.get("style")
            sports_array = [s.strip() for s in sports_input.split(',')] if isinstance(sports_input, str) else sports_input
            update_fields["enrolled_sports"] = sports_array
            update_fields["style"] = ", ".join(sports_array)

        if getattr(request.user, 'role', '') == 'SUPER_ADMIN' and "branch_name" in request.data:
            update_fields["branch_name"] = request.data.get("branch_name").strip().upper()

        try:
            db['students'].update_one({"_id": ObjectId(student_id)}, {"$set": update_fields})
            return Response({"message": "Student profile updated."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        if getattr(request.user, 'role', '') != 'SUPER_ADMIN':
            return Response({"error": "Only Admins can delete profiles."}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get("student_id")
        if not student_id:
            return Response({"error": "Student ID required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            db.students.delete_one({"_id": ObjectId(student_id)})
            db.attendance.delete_many({"student_id": ObjectId(student_id)})
            db.payments.delete_many({"student_id": str(student_id)})
            return Response({"message": "Student permanently deleted."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentPromoteView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def post(self, request):
        if getattr(request.user, 'role', '') != 'SUPER_ADMIN':
            return Response({"error": "Only Admins can promote students."}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get("student_id")
        new_belt = request.data.get("new_belt")

        if not student_id or not new_belt:
            return Response({"error": "Student ID and New Belt required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            db.students.update_one(
                {"_id": ObjectId(student_id)},
                {"$set": {"current_belt": str(new_belt).strip().upper()}}
            )
            return Response({"message": f"Promoted to {new_belt}"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)