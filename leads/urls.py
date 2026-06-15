# Location: leads/urls.py

from django.urls import path
from .views import LeadPipelineView
from students.views_export import EnterpriseDataExportView # Point to your global export engine

urlpatterns = [
    # Resolves: /api/leads/
    path('leads/', LeadPipelineView.as_view(), name='lead_pipeline_root'),
    
    # Resolves: /api/leads/export/
    path('leads/export/', EnterpriseDataExportView.as_view(), {'target_module': 'leads'}, name='export_leads_data'),
]