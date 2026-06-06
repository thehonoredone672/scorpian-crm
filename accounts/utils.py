import bcrypt
import jwt
import datetime
from django.conf import settings

def hash_password(plain_text_password: str) -> str:
    """
    Hashes a password using a random salt and bcrypt.
    Transforms raw input into an irreversible cryptographic hash string.
    """
    salt = bcrypt.gensalt(rounds=12) # Enterprise standard computational cost
    hashed = bcrypt.hashpw(plain_text_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_text_password: str, hashed_password: str) -> bool:
    """
    Validates a raw password against the stored string hash safely.
    Prevents timing attacks via internal cryptographic string comparison.
    """
    return bcrypt.checkpw(
        plain_text_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def generate_jwt_token(user_id: str, role: str) -> str:
    """
    Generates a stateless JSON Web Token valid for 24 hours.
    Encodes user identification parameters into the token structure.
    """
    payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
        'iat': datetime.datetime.now(datetime.timezone.utc)
    }
    # Sign token securely using Django project-wide secret key
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')