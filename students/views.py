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
        

    def delete(self, request):
        if getattr(request.user, 'role', '') != 'SUPER_ADMIN':
            return Response({"error": "Only Admins can delete profiles."}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get("student_id")
        if not student_id:
            return Response({"error": "Student ID required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Delete the student, their attendance, and their payments
            db.students.delete_one({"_id": ObjectId(student_id)})
            db.attendance.delete_many({"student_id": ObjectId(student_id)})
            db.payments.delete_many({"student_id": str(student_id)})
            return Response({"message": "Student permanently deleted."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        # === AGGRESSIVE BRANCH RESOLUTION FIX ===
        instructor_branch = getattr(user, 'branch_name', None)
        if not instructor_branch and hasattr(user, 'dict'):
            instructor_branch = user.dict.get('branch_name')

        # Fallback 1: DB Lookup by ID
        if not instructor_branch:
            user_id = getattr(user, 'id', None) or (user.dict.get('_id') if hasattr(user, 'dict') else None)
            if user_id:
                try:
                    user_record = db.users.find_one({"_id": ObjectId(str(user_id))})
                    if user_record: instructor_branch = user_record.get('branch_name')
                except: pass

        # Fallback 2: DB Lookup by Email
        if not instructor_branch:
            user_email = getattr(user, 'email', None) or (user.dict.get('email') if hasattr(user, 'dict') else None)
            if user_email:
                user_record = db.users.find_one({"email": user_email})
                if user_record: instructor_branch = user_record.get('branch_name')

        if not instructor_branch:
            return Response({"error": "System Alert: Instructor profile is corrupted or missing a branch assignment. Please check the Instructor Roster."}, status=status.HTTP_400_BAD_REQUEST)

        instructor_branch = instructor_branch.strip().upper()
        # ========================================

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

        try:
            custom_fee = float(data.get("custom_fee", 0.00))
            update_fields["custom_fee"] = custom_fee
        except ValueError:
            pass

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