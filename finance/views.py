from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class InvoiceCreatePaymentView(APIView):
    """
    Core API Controller for SRS Module 7 (Fee Management).
    Tracks double-entry style debits (Invoices) and credits (Payments) inside MongoDB.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        """Fetches the comprehensive financial ledger stream across the active branch tenant context."""
        user = request.user
        query = {}

        # Maintain multi-tenant operational security isolation
        if user.role != 'SUPER_ADMIN' and hasattr(user, 'branch_id'):
            query["branch_id"] = ObjectId(user.branch_id)

        try:
            ledger_cursor = db['payments'].find(query)
            ledger_payload = []

            for tx in ledger_cursor:
                ledger_payload.append({
                    "_id": str(tx.get('_id')),
                    "student_id": str(tx.get('student_id')),
                    "branch_id": str(tx.get('branch_id')) if tx.get('branch_id') else None,
                    "amount": float(tx.get('amount', 0.00)),
                    "type": tx.get('type', 'DEBIT'), # DEBIT = Invoice Issued, CREDIT = Payment Paid
                    "payment_mode": tx.get('payment_mode', 'UPI'), # UPI, CASH, BANK_TRANSFER, CARD
                    "description": tx.get('description', 'Monthly Training Fee Partition'),
                    "timestamp": tx.get('payment_date', datetime.datetime.utcnow().isoformat())
                })
            
            # Returns the ledger stream reverse-chronologically
            return Response(ledger_payload[::-1], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Ledger system aggregate fetch aborted: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Commits a brand-new financial transaction directly into the immutable ledger blocks."""
        user = request.user
        data = request.data

        # Explicit payload data checks
        student_id = data.get('student_id')
        amount = data.get('amount')
        tx_type = data.get('type') # EXPECTS: "DEBIT" or "CREDIT"

        if not student_id or amount is None or not tx_type:
            return Response({"error": "Missing transaction parameters: student_id, amount, and type are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tx_document = {
                "student_id": ObjectId(student_id),
                "amount": float(amount),
                "type": tx_type.upper(),
                "payment_mode": data.get('payment_mode', 'UPI').upper(),
                "description": data.get('description', 'Training Fee Apportionment').strip(),
                "payment_date": datetime.datetime.utcnow().isoformat(),
                "branch_id": ObjectId(user.branch_id) if hasattr(user, 'branch_id') else None
            }

            result = db['payments'].insert_one(tx_document)
            return Response({
                "message": "Financial parameter logged safely to cloud database partition.",
                "tx_id": str(result.inserted_id)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Ledger transactional logging execution aborted: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)