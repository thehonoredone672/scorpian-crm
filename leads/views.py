from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class LeadPipelineView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        user = request.user
        query = {}
        
        # Isolate leads by branch for instructors
        if user.role != 'SUPER_ADMIN':
            query["branch_name"] = getattr(user, 'branch_name', 'COIMBATORE')

        try:
            leads = []
            for l in db['leads'].find(query):
                leads.append({
                    "id": str(l["_id"]),
                    "name": l.get("name", ""),
                    "phone": l.get("phone", ""),
                    "program": l.get("program", "General"),
                    "source": l.get("source", "Walk-in"),
                    "status": l.get("status", "NEW"),
                    "notes": l.get("notes", "")
                })
            return Response(leads, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user = request.user
        data = request.data
        
        branch_assignment = "COIMBATORE" if user.role == 'SUPER_ADMIN' else getattr(user, 'branch_name', 'COIMBATORE')

        new_lead = {
            "name": data.get("name"),
            "phone": data.get("phone"),
            "program": data.get("program", "General"),
            "source": data.get("source", "Walk-in"),
            "status": "NEW",
            "notes": "",
            "branch_name": branch_assignment,
            "created_at": datetime.datetime.utcnow()
        }
        db['leads'].insert_one(new_lead)
        return Response({"message": "Lead captured."}, status=status.HTTP_201_CREATED)

    def put(self, request):
        """Allows updating of Lead status and sales notes from the drawer UI."""
        data = request.data
        lead_id = data.get("lead_id")
        
        if not lead_id:
            return Response({"error": "Lead ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        update_fields = {
            "status": data.get("status", "NEW"),
            "notes": data.get("notes", ""),
            "updated_at": datetime.datetime.utcnow()
        }

        try:
            result = db['leads'].update_one(
                {"_id": ObjectId(lead_id)},
                {"$set": update_fields}
            )
            if result.matched_count == 0:
                return Response({"error": "Lead not found."}, status=status.HTTP_404_NOT_FOUND)
                
            return Response({"message": "Lead updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)