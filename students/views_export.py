import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from database.mongodb_client import db
from accounts.authentication import MongoJWTAuthentication
from bson import ObjectId

class EnterpriseDataExportView(APIView):
    """
    Core API Controller for SRS Module 16 (Export System).
    Generates dynamic, on-demand CSV streams directly from MongoDB data clusters.
    """
    authentication_classes = [MongoJWTAuthentication]

    def get(self, request, target_module):
        """
        Generates and streams structured CSV files based on url parameters.
        Allowed pathways: 'students', 'leads', 'ledger'
        """
        user = request.user
        
        # Define clean tenant boundary constraint matching your isolation profile
        scope_query = {}
        if user.role in ['BRANCH_MANAGER', 'INSTRUCTOR'] and hasattr(user, 'branch_id'):
            scope_query["branch_id"] = ObjectId(user.branch_id)

        # -------------------------------------------------------------
        # BRANCH 1: STUDENTS INDEX EXPORT
        # -------------------------------------------------------------
        if target_module == 'students':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="scorpion_students_manifest.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['System ID', 'First Name', 'Last Name', 'Phone', 'Style Path', 'Current Rank Status'])
            
            records = db['students'].find(scope_query)
            for item in records:
                writer.writerow([
                    str(item.get('_id')),
                    item.get('first_name', ''),
                    item.get('last_name', ''),
                    f"'{item.get('phone', '')}", # Quote prefix prevents Excel from truncating leading zeros
                    item.get('style', 'Karate'),
                    item.get('current_belt', 'WHITE')
                ])
            return response

        # -------------------------------------------------------------
        # BRANCH 2: SALES LEADS PIPELINE EXPORT
        # -------------------------------------------------------------
        elif target_module == 'leads':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="scorpion_leads_pipeline.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Lead ID Code', 'Full Name', 'Contact Number', 'Program Track', 'Pipeline Status'])
            
            records = db['leads'].find(scope_query)
            for item in records:
                writer.writerow([
                    item.get('lead_id', 'N/A'),
                    item.get('name', ''),
                    f"'{item.get('phone', '')}",
                    item.get('program', 'General'),
                    item.get('status', 'NEW')
                ])
            return response

        # -------------------------------------------------------------
        # BRANCH 3: FINANCIAL ACCOUNTING LEDGER EXPORT
        # -------------------------------------------------------------
        elif target_module == 'ledger':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="scorpion_financial_ledger.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Transaction Hash ID', 'Description Entry', 'Mode', 'Associated Student Cloud ID', 'Amount (INR)', 'Entry Type'])
            
            records = db['payments'].find(scope_query)
            for item in records:
                writer.writerow([
                    str(item.get('_id')),
                    item.get('description', ''),
                    item.get('payment_mode', 'UPI'),
                    str(item.get('student_id', '')),
                    float(item.get('amount', 0.00)),
                    item.get('type', 'DEBIT')
                ])
            return response

        else:
            return HttpResponse("Target data collection layer route context unrecognized.", status=400)