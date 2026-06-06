from django.urls import path
from .views import SportListCreateView

urlpatterns = [
    path('', SportListCreateView.as_view(), name='sports_list_create'),
]