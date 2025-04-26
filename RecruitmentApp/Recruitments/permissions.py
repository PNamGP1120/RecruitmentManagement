from rest_framework import permissions
from .models import Role, UserRole

class IsNTVUser(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng có vai trò là Người tìm việc (NTV).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.NTV).exists()

class IsNTDUser(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng có vai trò là Nhà tuyển dụng (NTD).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.NTD).exists()

class IsAdminUser(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng có vai trò là Quản trị viên (Admin).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.ADMIN).exists()

class IsApprovedNTDUser(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng có vai trò là Nhà tuyển dụng (NTD) và đã được phê duyệt.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.NTD, isApproved=True).exists()

class IsOwner(permissions.BasePermission):
    """
    Cho phép truy cập nếu người dùng là chủ sở hữu của đối tượng.
    """
    def has_object_permission(self, request, view, obj):
        # Kiểm tra quyền sở hữu dựa trên các trường khác nhau tùy thuộc vào model
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'ntv_profile') and hasattr(obj.ntv_profile, 'user'):
            return obj.ntv_profile.user == request.user
        elif hasattr(obj, 'ntd_profile') and hasattr(obj.ntd_profile, 'user'):
            return obj.ntd_profile.user == request.user
        return False

class IsNTVUserOrReadOnly(permissions.BasePermission):
    """
    Cho phép người dùng NTV tạo/chỉnh sửa, và tất cả mọi người đều có thể đọc.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                (request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.NTV).exists()))

class IsNTDUserOrReadOnly(permissions.BasePermission):
    """
    Cho phép người dùng NTD tạo/chỉnh sửa, và tất cả mọi người đều có thể đọc.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                (request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.NTD).exists()))

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Cho phép người dùng Admin tạo/chỉnh sửa, và tất cả mọi người đều có thể đọc.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                (request.user.is_authenticated and hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__roleName=Role.ADMIN).exists()))