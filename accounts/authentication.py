import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from database.mongodb_client import db

class StatelessMongoUser:
    """
    Upgraded memory-resident user object that now supports tenant tracking.
    """
    def __init__(self, user_id, role, branch_id=None):
        self.id = user_id
        self.role = role
        self.branch_id = branch_id  # New: Tracks tenant isolation scope
        self.is_authenticated = True

class MongoJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            header_parts = auth_header.split()
            if len(header_parts) != 2 or header_parts[0].lower() != 'bearer':
                raise exceptions.AuthenticationFailed("Malformed Authorization header token format.")
                
            token = header_parts[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Access token has expired.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Cryptographic signature mismatch.")

        # Extract branch_id if it exists in the token (Super Admins won't have one)
        user = StatelessMongoUser(
            user_id=payload.get('user_id'),
            role=payload.get('role'),
            branch_id=payload.get('branch_id') # Injects the silo constraint into memory
        )
        
        return (user, token)