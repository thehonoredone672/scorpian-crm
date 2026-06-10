# Location: leads/urls.py

from django.urls import path
from .views import LeadPipelineView

urlpatterns = [
    # This combines with the root path to form exactly: /api/leads/
    path('leads/', LeadPipelineView.as_view(), name='lead-pipeline'),
]