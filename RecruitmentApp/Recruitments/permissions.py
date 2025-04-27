from rest_framework import permissions

# Quyền chung cho người dùng đã xác thực
class IsAuthenticatedUser(permissions.BasePermission):
    """
    Cho phép truy cập chỉ khi người dùng đã xác thực.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

# Quyền cho người dùng là Admin
class IsAdminUser(permissions.IsAdminUser):
    pass

# Quyền cho người dùng có vai trò NTD đang hoạt động
class IsNtdUser(permissions.BasePermission):
    """
    Cho phép truy cập chỉ khi người dùng đã xác thực và có vai trò NTD đang hoạt động.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD'

# Quyền cho người dùng có vai trò NTV đang hoạt động
class IsNtvUser(permissions.BasePermission):
    """
    Cho phép truy cập chỉ khi người dùng đã xác thực và có vai trò NTV đang hoạt động.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'ntvprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTV'

# Quyền cho phép bất kỳ ai (cho đăng ký)
class AllowAny(permissions.AllowAny):
    pass

# Quyền cho chủ sở hữu đối tượng hoặc admin
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Cho phép chủ sở hữu đối tượng hoặc admin có quyền truy cập.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Cần điều chỉnh tùy theo model và quyền sở hữu cụ thể
        return obj.user == request.user or request.user.is_staff

# Quyền cho người nhận thông báo
class IsRecipient(permissions.BasePermission):
    """
    Cho phép người dùng chỉ truy cập vào thông báo của chính họ.
    """
    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user

# Quyền tùy chỉnh cho API đăng ký
class RegisterUserPermission(AllowAny):
    pass

# Quyền tùy chỉnh cho API trở thành NTD
class IsAuthenticatedAndNotNtd(IsAuthenticatedUser):
    """
    Cho phép truy cập chỉ khi người dùng đã xác thực và chưa có vai trò NTD hoạt động.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return not hasattr(request.user, 'ntdprofile') and (not request.user.activeRole or request.user.activeRole.roleName != 'NTD')

class BecomeNtdPermission(IsAuthenticatedAndNotNtd):
    pass

# Quyền tùy chỉnh cho API trở thành NTV
class IsAuthenticatedAndNotNtv(IsAuthenticatedUser):
    """
    Cho phép truy cập chỉ khi người dùng đã xác thực và chưa có vai trò NTV hoạt động.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return not hasattr(request.user, 'ntvprofile') and (not request.user.activeRole or request.user.activeRole.roleName != 'NTV')

class BecomeNtvPermission(IsAuthenticatedAndNotNtv):
    pass

# Quyền tùy chỉnh cho API phê duyệt vai trò NTD
class IsAdminOrReadOnly(IsAdminUser):
    """
    Cho phép admin có toàn quyền.
    """
    pass

class ApproveNtdRolePermission(IsAdminOrReadOnly):
    pass

# Quyền tùy chỉnh cho API chuyển đổi activeRole
class CanSwitchRolePermission(IsAuthenticatedUser):
    """
    Cho phép người dùng đã xác thực chuyển đổi activeRole (cần kiểm tra logic trong view).
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view)

class SwitchActiveRolePermission(CanSwitchRolePermission):
    pass

# Quyền tùy chỉnh cho API quản lý Tin tuyển dụng
class JobPostingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and hasattr(request.user, 'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD'
        elif view.action in ['list', 'retrieve']:
            return True  # Hoặc IsAuthenticatedUser nếu bạn muốn bảo vệ việc xem
        elif view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_authenticated
        elif view.action == 'approve': # Endpoint phê duyệt riêng cho admin
            return request.user.is_staff
        return False

    def has_object_permission(self, request, view, obj):
        if view.action in permissions.SAFE_METHODS:
            return True
        elif view.action in ['update', 'partial_update', 'destroy']:
            return hasattr(obj, 'ntd_profile') and obj.ntd_profile.user == request.user
        elif view.action == 'approve':
            return request.user.is_staff
        return False

class JobPostingCreatePermission(IsNtdUser):
    pass

class JobPostingDetailPermission(IsOwnerOrAdmin):
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'ntd_profile') and (obj.ntd_profile.user == request.user or request.user.is_staff)

class JobPostingAdminPermission(IsAdminUser):
    pass

# Quyền tùy chỉnh cho API quản lý CV
class CvPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and hasattr(request.user, 'ntvprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTV'
        elif view.action in ['list']: # Admin xem danh sách
            return request.user.is_staff
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return request.user.is_authenticated
        return False

    def has_object_permission(self, request, view, obj):
        if view.action in permissions.SAFE_METHODS:
            return hasattr(obj, 'ntv_profile') and (obj.ntv_profile.user == request.user or request.user.is_staff)
        elif view.action in ['update', 'partial_update', 'destroy']:
            return hasattr(obj, 'ntv_profile') and obj.ntv_profile.user == request.user
        return False

class CvCreatePermission(IsNtvUser):
    pass

class CvDetailPermission(IsOwnerOrAdmin):
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'ntv_profile') and (obj.ntv_profile.user == request.user or request.user.is_staff)

class CvAdminListPermission(IsAdminUser):
    pass

# Quyền tùy chỉnh cho API Ứng tuyển
class ApplicationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and hasattr(request.user, 'ntvprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTV'
        elif view.action == 'list': # NTD xem ứng tuyển cho tin của họ
            return request.user.is_authenticated and hasattr(request.user, 'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD'
        elif view.action == 'retrieve': # Chi tiết ứng tuyển (có thể cho cả NTV và NTD liên quan)
            return request.user.is_authenticated
        elif view.action == 'destroy': # Chỉ admin mới được xóa
            return request.user.is_staff
        return False

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return obj.user == request.user or (hasattr(obj.job_posting, 'ntd_profile') and obj.job_posting.ntd_profile.user == request.user)
        return False

class ApplicationCreatePermission(IsNtvUser):
    pass

class ApplicationListNtdPermission(IsAuthenticatedUser, IsNtdUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # Logic bổ sung có thể cần để lọc ứng tuyển theo tin tuyển dụng của NTD trong view
        return True

class ApplicationDetailPermission(IsAuthenticatedUser):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or (hasattr(obj.job_posting, 'ntd_profile') and obj.job_posting.ntd_profile.user == request.user)

class ApplicationAdminDeletePermission(IsAdminUser):
    pass

# Quyền tùy chỉnh cho API Phỏng vấn
class InterviewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated and hasattr(request.user, 'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD'
        elif view.action in ['list', 'retrieve', 'update', 'partial_update']:
            return request.user.is_authenticated
        return False

    def has_object_permission(self, request, view, obj):
        return obj.application.user == request.user or obj.application.job_posting.ntd_profile.user == request.user

class InterviewCreatePermission(IsAuthenticatedUser, IsNtdUser):
    pass

class InterviewDetailPermission(IsAuthenticatedUser):
    def has_object_permission(self, request, view, obj):
        return obj.application.user == request.user or obj.application.job_posting.ntd_profile.user == request.user

class InterviewUpdatePermission(IsAuthenticatedUser):
    def has_object_permission(self, request, view, obj):
        return hasattr(obj.application.job_posting, 'ntd_profile') and obj.application.job_posting.ntd_profile.user == request.user

# Quyền tùy chỉnh cho API Thông báo
class NotificationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated
        # Thường việc tạo thông báo sẽ không thông qua API người dùng thông thường

    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'update', 'partial_update']:
            return obj.recipient == request.user
        return False

class NotificationListPermission(IsAuthenticatedUser):
    pass

class NotificationDetailPermission(IsRecipient):
    pass

class NotificationUpdatePermission(IsRecipient):
    pass