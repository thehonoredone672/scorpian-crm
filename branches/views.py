from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId
import datetime

class BranchListCreateView(APIView):
    """
    Core engine for processing physical academy locations.
    Demonstrates dynamic query building for logical data isolation.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches branches based on the requester's clearance level."""
        user = request.user
        branches_collection = db['branches']
        
        # Base query (Only fetch active physical locations)
        query = {"status": "ACTIVE"}

        # LOGICAL ISOLATION FIREWALL
        if user.role == 'SUPER_ADMIN':
            pass # Super Admin sees all branches
            
        elif user.role == 'BRANCH_MANAGER':
            if not user.branch_id:
                return Response({"error": "Critical: Manager profile lacks branch assignment."}, status=status.HTTP_403_FORBIDDEN)
            # Constrain the query strictly to their assigned MongoDB ObjectId
            query["_id"] = ObjectId(user.branch_id)
            
        else:
            return Response({"error": "Unauthorized role clearance."}, status=status.HTTP_403_FORBIDDEN)

        # Execute query
        cursor = branches_collection.find(query)
        
        branches = []
        for branch in cursor:
            branch['_id'] = str(branch['_id'])
            branches.append(branch)
            
        return Response(branches, status=status.HTTP_200_OK)

    def post(self, request):
        """Allows Global Super Admins to provision a new physical franchise location."""
        # Only Corporate HQ (Super Admins) can open new branches
        if not IsSuperAdmin().has_permission(request, self):
            return Response({"error": "Unauthorized: Corporate clearance required to open branches."}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data
        name = data.get('name')
        branch_code = data.get('branch_code') # e.g., 'BR-DEL-01'
        city = data.get('city')

        if not name or not branch_code:
            return Response({"error": "Branch name and unique branch_code are required."}, status=status.HTTP_400_BAD_REQUEST)

        branches_collection = db['branches']
        
        # Enforce unique branch codes to prevent billing conflicts
        if branches_collection.find_one({"branch_code": branch_code.strip()}):
            return Response({"error": "A branch with this location code already exists."}, status=status.HTTP_400_BAD_REQUEST)

        new_branch = {
            "name": name.strip(),
            "branch_code": branch_code.strip().upper(),
            "address": {
                "city": city,
            },
            "status": "ACTIVE",
            "opening_date": datetime.datetime.now(datetime.timezone.utc),
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        result = branches_collection.insert_one(new_branch)
        return Response({
            "message": "Physical franchise location provisioned successfully.",
            "branch_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)