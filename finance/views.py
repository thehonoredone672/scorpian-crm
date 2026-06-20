from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime
import traceback

class FinanceLedgerView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request):
        try:
            # Safely fetch transactions and convert dates
            transactions = list(db['finance_ledger'].find().sort("created_at", -1).limit(100))
            for t in transactions: 
                t['id'] = str(t.pop('_id'))
                if 'student_id' in t: t['student_id'] = str(t['student_id'])
                if 'created_at' in t: 
                    t['created_at'] = t['created_at'].isoformat() if isinstance(t['created_at'], datetime.datetime) else str(t['created_at'])
            return Response(transactions, status=status.HTTP_200_OK)
        except Exception as e:
            print("LEDGER FETCH ERROR:", traceback.format_exc())
            return Response([], status=status.HTTP_200_OK) # Return empty list instead of crashing the UI

    def post(self, request):
        try:
            print("\n--- NEW PAYMENT REQUEST ---")
            data = request.data
            print("Data Received:", data)

            student_id = data.get('student_id')
            amount = data.get('amount')
            method = data.get('method', 'CASH')
            reference = data.get('reference', '')

            if not student_id or amount is None or amount == '':
                return Response({"error": "Student ID and Amount are required."}, status=status.HTTP_400_BAD_REQUEST)

            amount = float(amount)
            
            # 1. Verify Student Exists
            student = db['students'].find_one({"_id": ObjectId(str(student_id))})
            if not student:
                print("ERROR: Student not found in DB:", student_id)
                return Response({"error": "Student not found in database."}, status=status.HTTP_404_NOT_FOUND)

            # Extract Admin Name safely
            admin_name = 'Admin'
            if hasattr(request.user, 'dict'): admin_name = request.user.dict.get('name', 'Admin')
            elif getattr(request.user, 'name', None): admin_name = request.user.name

            # 2. Record the Transaction
            transaction = {
                "student_id": ObjectId(str(student_id)),
                "student_name": f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
                "branch_name": student.get('branch_name', 'UNKNOWN'),
                "amount": amount,
                "method": str(method).upper(),
                "reference": str(reference),
                "processed_by": admin_name,
                "created_at": datetime.datetime.utcnow(),
                "date_string": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            db['finance_ledger'].insert_one(transaction)
            print("SUCCESS: Transaction saved to DB.")

            # 3. Smart Math (Update Student Balance)
            current_balance = float(student.get('outstanding_balance', 0))
            new_balance = max(0.0, current_balance - amount) 
            
            # Restore status if debt is cleared
            current_status = student.get('status', 'ACTIVE')
            new_status = 'ACTIVE' if (new_balance <= 0 and current_status == 'PENDING') else current_status
            
            db['students'].update_one(
                {"_id": ObjectId(str(student_id))},
                {"$set": {"outstanding_balance": new_balance, "status": new_status}}
            )
            print(f"SUCCESS: Student balance updated to {new_balance}.")
            print("---------------------------\n")

            return Response({"message": "Payment recorded.", "new_balance": new_balance}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("PAYMENT CRASH:", traceback.format_exc())
            return Response({"error": "Server crashed processing payment. Check terminal."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)