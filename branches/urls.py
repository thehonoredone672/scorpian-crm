from django.urls import path
from .views import BranchListCreateView

urlpatterns = [
    path('', BranchListCreateView.as_view(), name='branches_list_create'),
]