from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId
import datetime

class InvoiceCreatePaymentView(APIView):
    """
    Enterprise ledger controller handling debit generation and credit matching.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches financial transaction history bounded tightly by tenant rules."""
        user = request.user
        ledger_collection = db['ledger']
        
        query = {}
        if user.role == 'SUPER_ADMIN':
            pass # Corporate visibility
        elif user.role == 'BRANCH_MANAGER':
            query["branch_id"] = ObjectId(user.branch_id) # Siloed visibility
        else:
            return Response({"error": "Access Denied: Financial clearance required."}, status=status.HTTP_403_FORBIDDEN)

        cursor = ledger_collection.find(query).sort("timestamp", -1)
        
        records = []
        for row in cursor:
            row['_id'] = str(row['_id'])
            row['student_id'] = str(row['student_id'])
            row['branch_id'] = str(row['branch_id'])
            records.append(row)
            
        return Response(records, status=status.HTTP_200_OK)

    def post(self, request):
        """Creates a brand new debit invoice or payments credit entry into the ledger."""
        user = request.user
        data = request.data
        
        student_id_str = data.get('student_id')
        amount = data.get('amount') # Store as base integer units
        transaction_type = data.get('type') # DEBIT (Fee Due) or CREDIT (Payment Made)
        description = data.get('description', 'Monthly Tuition Fee')

        if not all([student_id_str, amount, transaction_type]):
            return Response({"error": "Missing ledger attributes: student_id, amount, type required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_obj_id = ObjectId(student_id_str)
        except Exception:
            return Response({"error": "Malformed Student ID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Confirm student existence and extract branch context
        student = db['students'].find_one({"_id": student_obj_id})
        if not student:
            return Response({"error": "Target student profile not found."}, status=status.HTTP_404_NOT_FOUND)

        branch_obj_id = student['branch_id']

        # Tenant Security Enforcement Check
        if user.role == 'BRANCH_MANAGER' and str(branch_obj_id) != user.branch_id:
            return Response({"error": "Unauthorized: Student belongs to an alternate branch silo."}, status=status.HTTP_403_FORBIDDEN)

        new_transaction = {
            "student_id": student_obj_id,
            "branch_id": branch_obj_id,
            "amount": float(amount),
            "type": transaction_type.upper(), # DEBIT / CREDIT
            "description": description.strip(),
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }

        result = db['ledger'].insert_one(new_transaction)
        return Response({
            "message": "Financial ledger entry written securely to the cloud cluster.",
            "transaction_id": str(result.inserted_id)
        }, status=status.HTTP_201_CREATED)