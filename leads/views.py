from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import uuid

class LeadPipelineView(APIView):
    """
    Core API Controller for SRS Module 3 (Lead Management).
    Handles secure data storage and multitenant branch isolation.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches all active leads mapped to the user's operational branch."""
        user = request.user
        query = {}

        # Enforce strict branch tenant isolation for instructors/managers
        if user.role in ['BRANCH_MANAGER', 'INSTRUCTOR'] and hasattr(user, 'branch_id'):
            query["branch_id"] = ObjectId(user.branch_id)

        try:
            leads_cursor = db['leads'].find(query)
            leads_data = []
            
            for lead in leads_cursor:
                leads_data.append({
                    "id": str(lead.get('_id')),
                    "lead_id": lead.get('lead_id', 'N/A'),
                    "name": lead.get('name'),
                    "age": lead.get('age'),
                    "gender": lead.get('gender'),
                    "phone": lead.get('phone'),
                    "whatsapp": lead.get('whatsapp'),
                    "program": lead.get('program'),
                    "status": lead.get('status', 'NEW')
                })
            return Response(leads_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Database read failure: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Captures a new lead and assigns an automated unique Lead ID string."""
        user = request.user
        data = request.data

        # Explicit validation parameters checking
        if not data.get('name') or not data.get('phone'):
            return Response({"error": "Missing critical parameters: name and phone are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Build clean Mongo document object structure mapping directly to your SRS
        lead_document = {
            "lead_id": f"L-{uuid.uuid4().hex[:6].upper()}", # Auto-generated unique tracking tag
            "name": data.get('name'),
            "age": data.get('age', 0),
            "gender": data.get('gender', 'MALE'),
            "phone": data.get('phone'),
            "whatsapp": data.get('whatsapp', data.get('phone')),
            "program": data.get('program', 'General'),
            "status": data.get('status', 'NEW'),
            "branch_id": ObjectId(user.branch_id) if hasattr(user, 'branch_id') else None
        }

        try:
            result = db['leads'].insert_one(lead_document)
            return Response({
                "message": "Lead captured successfully.",
                "id": str(result.inserted_id),
                "lead_id": lead_document["lead_id"]
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Database write transaction aborted: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)