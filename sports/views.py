from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId
import datetime

class SportListCreateView(APIView):
    """
    API Dashboard configuration layer for processing global sports matrices.
    """
    # Protect this entire endpoint via our custom security modules
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches all active sports registered across the franchise."""
        sports_collection = db['sports']
        # Find all sports where status is NOT 'ARCHIVED'
        cursor = sports_collection.find({"status": {"$ne": "ARCHIVED"}})
        
        sports_list = []
        for sport in cursor:
            sport['_id'] = str(sport['_id']) # Convert ObjectId to safe JSON string string
            sports_list.append(sport)
            
        return Response(sports_list, status=status.HTTP_200_OK)

    def post(self, request):
        """Allows Global Super Admins to dynamically provision a new sport module."""
        # Force strict role enforcement checks dynamically
        if not IsSuperAdmin().has_permission(request, self):
            return Response({"error": "Unauthorized: Super Admin access privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data
        name = data.get('name')
        description = data.get('description')
        color_theme = data.get('color_theme', '#FFBD59') # Falls back to Scorpion Amber

        if not name:
            return Response({"error": "Sport name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        sports_collection = db['sports']
        
        if sports_collection.find_one({"name": name.strip()}):
            return Response({"error": "A sport with this profile identifier name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        new_sport = {
            "name": name.strip(),
            "description": description,
            "color_theme": color_theme,
            "status": "ACTIVE",
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        result = sports_collection.insert_one(new_sport)
        return Response({
            "message": "Sport engine initialized successfully.",
            "sport_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)