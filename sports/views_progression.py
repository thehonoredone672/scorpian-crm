from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId

class ProgressionEngineView(APIView):
    """
    Handles dynamic, code-free ranking matrices for individual sports.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, sport_id):
        """Fetches all ranking tiers for a specified sport, ordered sequentially."""
        try:
            sport_obj_id = ObjectId(sport_id)
        except Exception:
            return Response({"error": "Malformed String: Invalid Sport ID format."}, status=status.HTTP_400_BAD_REQUEST)

        progression_collection = db['progression_levels']
        # Fetch rankings and sort them sequentially using MongoDB's .sort()
        cursor = progression_collection.find({"sport_id": sport_obj_id}).sort("level_order", 1)
        
        levels = []
        for level in cursor:
            level['_id'] = str(level['_id'])
            level['sport_id'] = str(level['sport_id'])
            levels.append(level)
            
        return Response(levels, status=status.HTTP_200_OK)

    def post(self, request, sport_id):
        """Allows creation of unique progression levels linked to a specific sport."""
        if not IsSuperAdmin().has_permission(request, self):
            return Response({"error": "Privileged Action Restricted to Super Admin."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            sport_obj_id = ObjectId(sport_id)
        except Exception:
            return Response({"error": "Invalid Sport ID mapping target parameter."}, status=status.HTTP_400_BAD_REQUEST)

        # Confirm the parent sport actually exists first
        if not db['sports'].find_one({"_id": sport_obj_id}):
            return Response({"error": "Parent sport engine mapping target not found."}, status=status.HTTP_444_NOT_RESPONSE if hasattr(status, 'HTTP_444_NOT_RESPONSE') else status.HTTP_404_NOT_FOUND)

        data = request.data
        level_name = data.get('level_name')
        level_order = data.get('level_order') # Integer ordering tier (e.g. 1=White, 2=Yellow)
        minimum_months = data.get('minimum_months', 0)
        attendance_pct = data.get('required_attendance_pct', 80)

        if not level_name or level_order is None:
            return Response({"error": "Missing level structural tracking attributes: level_name, level_order"}, status=status.HTTP_400_BAD_REQUEST)

        new_level = {
            "sport_id": sport_obj_id,
            "level_name": level_name.strip(),
            "level_order": int(level_order),
            "requirements": {
                "minimum_months": int(minimum_months),
                "required_attendance_pct": int(attendance_pct)
            }
        }

        result = db['progression_levels'].insert_one(new_level)
        return Response({
            "message": "Progression level structural metric mapped successfully.",
            "level_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)