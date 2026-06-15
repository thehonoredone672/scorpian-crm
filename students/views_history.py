from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId
import datetime

class StudentHistoryView(APIView):
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, student_id):
        try:
            s_obj_id = ObjectId(student_id)
            
            # Fetch last 5 attendance logs
            att_cursor = db['attendance'].find({"student_id": s_obj_id}).sort("date", -1).limit(5)
            attendance = [{"date": a.get("date"), "status": a.get("status")} for a in att_cursor]
            
            # Fetch last 5 payment logs (checks both ObjectId and string mappings defensively)
            fee_cursor = db['payments'].find({
                "student_id": {"$in": [str(student_id), s_obj_id]}, 
                "type": "CREDIT"
            }).sort("timestamp", -1).limit(5)
            
            fees = []
            for f in fee_cursor:
                # Format dates cleanly for UI
                raw_date = f.get("timestamp", f.get("date", "Unknown"))
                if isinstance(raw_date, datetime.datetime):
                    clean_date = raw_date.strftime("%Y-%m-%d")
                elif isinstance(raw_date, str) and "T" in raw_date:
                    clean_date = raw_date.split("T")[0]
                else:
                    clean_date = str(raw_date)

                fees.append({
                    "date": clean_date,
                    "amount": f.get("amount")
                })
            
            return Response({"attendance": attendance, "fees": fees}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to load CRM history: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)