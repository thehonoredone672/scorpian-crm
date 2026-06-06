from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Enforces authorization rules specifically for Global Administrators.
    """
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, 'role', None) == 'SUPER_ADMIN')

class IsBranchManager(BasePermission):
    """
    Enforces authorization rules for Branch Managers.
    """
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, 'role', None) == 'BRANCH_MANAGER')