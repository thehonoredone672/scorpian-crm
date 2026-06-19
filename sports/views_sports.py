from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId
import datetime

class SportsManagementView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        sports_cursor = db['sports'].find()
        sports_list = []
        for sport in sports_cursor:
            sport['id'] = str(sport.get('_id'))
            if '_id' in sport:
                sport['_id'] = str(sport['_id'])
            sport['student_count'] = db['students'].count_documents({
                "status": "ACTIVE",
                "enrolled_sports": sport.get('name')
            })
            sports_list.append(sport)
        return Response(sports_list, status=status.HTTP_200_OK)

    def post(self, request):
        if not IsSuperAdmin().has_permission(request, self):
            return Response({"error": "Unauthorized: Super Admin access privileges required."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        name = data.get('name')
        if not name:
            return Response({"error": "Sport name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        name_capitalized = str(name).strip().capitalize()

        sports_collection = db['sports']
        if sports_collection.find_one({"name": name_capitalized}):
            return Response({"error": "A sport with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        new_sport = {
            "name": name_capitalized,
            "status": "ACTIVE",
            "created_at": datetime.datetime.utcnow()
        }
        result = sports_collection.insert_one(new_sport)
        return Response({
            "message": "Sport created successfully.",
            "sport_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        if not IsSuperAdmin().has_permission(request, self):
            return Response({"error": "Unauthorized: Super Admin access privileges required."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        name = data.get('name')
        if not name:
            name = request.query_params.get('name')
        if not name:
            return Response({"error": "Sport name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        name_capitalized = str(name).strip().capitalize()
        sports_collection = db['sports']
        
        result = sports_collection.delete_many({"name": name_capitalized})
        if result.deleted_count == 0:
            result = sports_collection.delete_many({"name": str(name).strip()})

        return Response({"message": "Sport deleted successfully."}, status=status.HTTP_200_OK)


class SportRosterView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, sport_name):
        query = {
            "status": "ACTIVE",
            "enrolled_sports": sport_name
        }
        students_cursor = db['students'].find(query)
        students_list = []
        for s in students_cursor:
            s['id'] = str(s.get('_id'))
            if '_id' in s:
                s['_id'] = str(s['_id'])
            if 'created_at' in s:
                s['created_at'] = str(s['created_at'])
            students_list.append(s)

        students_list.sort(key=lambda x: str(x.get('first_name', '')).lower())
        return Response(students_list, status=status.HTTP_200_OK)
