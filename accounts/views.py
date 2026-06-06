from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import datetime
from database.mongodb_client import db
from .utils import hash_password, check_password, generate_jwt_token

class RegisterAdminView(APIView):
    """
    Provisioning engine for the global Super Admin accounts.
    """
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            return Response({"error": "Missing required fields: name, email, password"}, status=status.HTTP_400_BAD_REQUEST)

        # Access MongoDB via our clean package-level shortcut
        users_collection = db['users']

        # Enforce unique index mapping via logic checks
        if users_collection.find_one({"email": email}):
            return Response({"error": "A user with this email identifier already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Assemble document payload structure
        new_user = {
            "name": name,
            "email": email,
            "password": hash_password(password),
            "role": "SUPER_ADMIN", # Initial bootstrap account setup privileges
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        result = users_collection.insert_one(new_user)

        return Response({
            "message": "Super Admin profile securely initialized inside cloud cluster.",
            "user_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Validates credentials and issues an access token.
    """
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required parameters"}, status=status.HTTP_400_BAD_REQUEST)

        users_collection = db['users']
        user = users_collection.find_one({"email": email})

        # Match hashed context parameters safely
        if not user or not check_password(password, user['password']):
            return Response({"error": "Invalid administrative credentials provided"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate access token
        token = generate_jwt_token(user['_id'], user.get('role', 'STAFF'))

        return Response({
            "message": "Authentication successful.",
            "access_token": token,
            "role": user.get('role')
        }, status=status.HTTP_200_OK)