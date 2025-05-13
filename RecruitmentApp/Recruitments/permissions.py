from rest_framework import permissions
from .models import UserRole, Role

class IsAdmin(permissions.BasePermission):
    """
    Cho phép chỉ người dùng có vai trò ADMIN thực hiện hành động.
    """
    def has_permission(self, request, view):
        return request.user.active_role and request.user.active_role.role_name == Role.Admin

class IsAuthenticated(permissions.BasePermission):
    """
    Cho phép người dùng đã đăng nhập thực hiện hành động.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class IsCreateOnly(permissions.BasePermission):
    """
    Cho phép người dùng thực hiện hành động POST (tạo mới), nhưng không cho phép các hành động khác.
    """
    def has_permission(self, request, view):
        return request.method == 'POST'

class IsUserOwner(permissions.BasePermission):
    """
    Cho phép người dùng chỉnh sửa thông tin của chính mình.
    """
    def has_object_permission(self, request, view, obj):
        return obj.my_user == request.user

class IsUserOwnerCV(permissions.BasePermission):
    """
    Cho phép người dùng chỉnh sửa CV của chính mình.
    """
    def has_object_permission(self, request, view, obj):
        return obj.job_seeker_profile.my_user == request.user

class IsUserOwnerJob(permissions.BasePermission):
    """
    Cho phép người dùng chỉnh sửa công việc của chính mình.
    """
    def has_object_permission(self, request, view, obj):
        return obj.recruiter_profile.my_user == request.user

class IsEmployer(permissions.BasePermission):
    """
    Cho phép chỉ người dùng có vai trò Nhà tuyển dụng (NTD) thực hiện hành động.
    """
    def has_permission(self, request, view):
        return request.user.active_role and request.user.active_role.role_name == Role.Recruiter

class IsJobSeeker(permissions.BasePermission):
    """
    Cho phép chỉ người dùng có vai trò Người tìm việc (NTV) thực hiện hành động.
    """
    def has_permission(self, request, view):
        return request.user.active_role and request.user.active_role.role_name == Role.JobSeeker

class IsApprovedUser(permissions.BasePermission):
    """
    Cho phép chỉ người dùng đã được phê duyệt thực hiện hành động.
    """
    def has_permission(self, request, view):
        user_role = UserRole.objects.filter(my_user=request.user, is_approved=True).first()
        return bool(user_role)

class IsAdminForUserRoleApproval(permissions.BasePermission):
    """
    Cho phép chỉ quản trị viên (ADMIN) phê duyệt hoặc từ chối yêu cầu nhà tuyển dụng.
    """
    def has_permission(self, request, view):
        return request.user.active_role and request.user.active_role.role_name == Role.Admin
