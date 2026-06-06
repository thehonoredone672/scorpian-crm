from django.urls import path
from .views import RegisterAdminView, LoginView

urlpatterns = [
    path('register-admin/', RegisterAdminView.as_view(), name='register_admin'),
    path('login/', LoginView.as_view(), name='login'),
]