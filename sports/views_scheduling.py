from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from accounts.permissions import IsSuperAdmin
from bson import ObjectId
import datetime

class BatchSchedulingView(APIView):
    """
    Automated configuration engine for generating recurring training schedules.
    """
    authentication_classes = [MongoJWTAuthentication]

    def post(self, request):
        user = request.user
        data = request.data
        
        sport_id_str = data.get('sport_id')
        branch_id_str = data.get('branch_id')
        batch_name = data.get('batch_name')
        days_of_week = data.get('days_of_week', [])  # Array of integers: 0=Monday, 2=Wednesday, etc.
        start_time_str = data.get('start_time')      # Format: "HH:MM" e.g., "07:00"

        if not all([sport_id_str, branch_id_str, batch_name, start_time_str]) or not days_of_week:
            return Response({"error": "Missing structural attributes. Required: sport_id, branch_id, batch_name, days_of_week, start_time"}, status=status.HTTP_400_BAD_REQUEST)

        # Tenant Security Enforcement Checks
        if user.role == 'BRANCH_MANAGER' and user.branch_id != branch_id_str:
            return Response({"error": "Unauthorized: Access restricted to your assigned branch silo."}, status=status.HTTP_403_FORBIDDEN)

        try:
            sport_obj_id = ObjectId(sport_id_str)
            branch_obj_id = ObjectId(branch_id_str)
        except Exception:
            return Response({"error": "Malformed ObjectId formatting parameters."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Store the Master Batch Template Record
        new_batch = {
            "batch_name": batch_name.strip(),
            "sport_id": sport_obj_id,
            "branch_id": branch_obj_id,
            "days_of_week": [int(d) for d in days_of_week],
            "start_time": start_time_str,
            "status": "ACTIVE",
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        batch_result = db['batches'].insert_one(new_batch)
        batch_id = batch_result.inserted_id

        # 2. THE AUTOMATED MULTI-FREQUENCY GENERATION LOOP (Look-Ahead Generator)
        # We look ahead 30 days and dynamically spawn actual session instances for the selected days
        session_instances = []
        start_date = datetime.date.today()
        
        for day_offset in range(30):
            current_date = start_date + datetime.timedelta(days=day_offset)
            # If the calendar day matches our chosen batch day metrics (0=Mon, 1=Tue...)
            if current_date.weekday() in new_batch["days_of_week"]:
                # Combine the calendar date string with our static batch time string
                session_time_str = f"{current_date.isoformat()}T{start_time_str}:00Z"
                
                session_instances.append({
                    "batch_id": batch_id,
                    "branch_id": branch_obj_id,
                    "sport_id": sport_obj_id,
                    "session_date": current_date.isoformat(),
                    "scheduled_time": session_time_str,
                    "attendance_records": [], # Initialized empty to accept student check-ins later
                    "status": "SCHEDULED"
                })

        # Bulk write the generated timeline grid into MongoDB Atlas
        if session_instances:
            db['sessions'].insert_many(session_instances)

        return Response({
            "message": "Master batch template saved and 30-day session roadmap generated.",
            "batch_id": str(batch_id),
            "sessions_spawned": len(session_instances)
        }, status=status.HTTP_201_CREATED)