from rest_framework import permissions

class IsVerifiedUser(permissions.BasePermission):
    """
    Allow access only to verified users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )

class IsCarrier(permissions.BasePermission):
    """
    Allow access only to carriers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'carrier'
        )

class IsCargoOwner(permissions.BasePermission):
    """
    Allow access only to cargo owners.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'cargo-owner'
        )

class IsLogisticsCompany(permissions.BasePermission):
    """
    Allow access only to logistics companies.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'logistics-company'
        )

class IsObjectOwner(permissions.BasePermission):
    """
    Allow access only to object owner.
    """
    def has_object_permission(self, request, view, obj):
        return bool(obj.owner == request.user)

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allow full access to staff users, but only read access to others.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class IsVerifiedOrReadOnly(permissions.BasePermission):
    """
    Allow full access to verified users, but only read access to others.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )