from rest_framework.views import APIView
from rest_framework.response import Response
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication

class BranchListView(APIView):
    """
    Returns a clean list of all branch names for global selection.
    Fixes the 403 Forbidden error for non-admin users.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        branches_collection = db['branches']
        # Query for all branches, only returning the name field and excluding _id
        cursor = branches_collection.find({}, {"_id": 0, "name": 1})
        
        branch_names = [branch['name'].upper() for branch in cursor if 'name' in branch]
        
        # Fallback to ["COIMBATORE"] if the collection is empty
        if not branch_names:
            branch_names = ["COIMBATORE"]
            
        return Response(branch_names)
