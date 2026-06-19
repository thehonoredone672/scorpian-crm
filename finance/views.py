from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class FinanceLedgerView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        # Fetch the latest 100 transactions
        transactions = list(db['finance_ledger'].find().sort("created_at", -1).limit(100))
        for t in transactions: 
            t['id'] = str(t.pop('_id'))
            if 'student_id' in t: t['student_id'] = str(t['student_id'])
        return Response(transactions, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        student_id = data.get('student_id')
        amount = data.get('amount')
        method = data.get('method', 'CASH')
        reference = data.get('reference', '')

        if not student_id or amount is None:
            return Response({"error": "Student ID and Amount are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
        except ValueError:
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Verify Student
        student = db['students'].find_one({"_id": ObjectId(str(student_id))})
        if not student:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Record the Transaction
        transaction = {
            "student_id": ObjectId(str(student_id)),
            "student_name": f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
            "branch_name": student.get('branch_name', 'UNKNOWN'),
            "amount": amount,
            "method": method.upper(),
            "reference": reference,
            "processed_by": getattr(request.user, 'name', 'System Admin'),
            "created_at": datetime.datetime.utcnow(),
            "date_string": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        db['finance_ledger'].insert_one(transaction)

        # 3. Smart Automation: Deduct Pending Months
        current_pending = int(student.get('pending_months', 0))
        if current_pending > 0:
            # Assuming 1 payment covers 1 month. You can adjust this math later if needed.
            new_pending = max(0, current_pending - 1) 
            
            # Auto-restore status to ACTIVE if they paid off their debt
            new_status = 'ACTIVE' if new_pending == 0 and student.get('status') == 'PENDING' else student.get('status')
            
            db['students'].update_one(
                {"_id": ObjectId(str(student_id))},
                {"$set": {"pending_months": new_pending, "status": new_status}}
            )

        return Response({"message": "Payment recorded successfully."}, status=status.HTTP_201_CREATED)