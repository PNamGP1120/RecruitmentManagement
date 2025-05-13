from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.utils import timezone
from firebase_admin import db
from rest_framework import status, generics, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

from .models import NtvProfile, Role, UserRole, Notification, NtdProfile, User, CV, JobPosting, Application, Interview, \
    Message
from .permissions import IsAuthenticated, IsCreateOnly, IsAdminForUserRoleApproval, IsAdmin, IsJobSeeker, IsUserOwnerCV, \
    IsEmployer
from .serializers import RegistrationSerializer, LoginSerializer, NtvProfileSerializer, NtdProfileSerializer, \
    UserSerializer, UserRoleSerializer, CVSerializer, JobPostingSerializer, ApplicationSerializer, InterviewSerializer, \
    MessageSerializer, ConversationSerializer


class RegistrationView(generics.CreateAPIView):
    """
    API đăng ký người dùng mới.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [IsCreateOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Đăng ký thành công!",
                "user": {"username": user.username, "email": user.email}
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    """
    API đăng nhập với JWT token.
    """
    serializer_class = LoginSerializer
    permission_classes = [IsCreateOnly]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"detail": "Username và password là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Thông tin đăng nhập không hợp lệ."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_200_OK)


class UpdateNtvProfileView(generics.GenericAPIView):
    """
    API để tạo mới hoặc cập nhật hồ sơ người tìm việc.
    """
    serializer_class = NtvProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.ntv_profile
        except NtvProfile.DoesNotExist:
            return NtvProfile.objects.create(user=user)

    def update(self, request, *args, **kwargs):
        ntv_profile = self.get_object()
        serializer = self.get_serializer(ntv_profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if ntv_profile.summary and ntv_profile.experience and ntv_profile.education:
            role, created = Role.objects.get_or_create(role_name=Role.NTV)
            user = request.user
            if user.active_role is None or user.active_role != role:
                user.active_role = role
                user.save()

            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={'is_approved': True, 'approved_at': timezone.now(), 'approved_by': user}
            )

            if not created and not user_role.is_approved:
                user_role.is_approved = True
                user_role.approved_at = timezone.now()
                user_role.approved_by = user
                user_role.save()

            return Response({
                "message": "Cập nhật hồ sơ thành công và vai trò 'Người tìm việc' đã được gán và phê duyệt.",
                "user": {"username": user.username, "email": user.email, "active_role": user.active_role.role_name},
                "ntv_profile": NtvProfileSerializer(ntv_profile).data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Cập nhật hồ sơ thành công, nhưng chưa đủ thông tin để gán vai trò 'Người tìm việc'."},
                status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class CreateNtdProfileView(generics.GenericAPIView):
    """
    API để nhập thông tin nhà tuyển dụng.
    """
    serializer_class = NtdProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.ntd_profile
        except NtdProfile.DoesNotExist:
            return None

    def update(self, request, *args, **kwargs):
        ntd_profile = self.get_object()
        if ntd_profile:
            serializer = self.get_serializer(ntd_profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            message = "Cập nhật hồ sơ nhà tuyển dụng thành công."
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            ntd_profile = serializer.save(user=request.user)
            message = "Thông tin nhà tuyển dụng đã được nhập. Yêu cầu phê duyệt đã được gửi đến admin."

        notification_to_user = Notification.objects.create(
            recipient=request.user,
            sender=request.user,
            message=f"{message} Yêu cầu của bạn đang chờ xác thực từ hệ thống.",
            type="System",
            related_url="/user/dashboard",
            is_read=False
        )

        admin_users = User.objects.filter(user_roles__role__role_name=Role.ADMIN)
        if not admin_users:
            return Response({"detail": "Không tìm thấy admin để gửi thông báo."}, status=status.HTTP_400_BAD_REQUEST)

        for admin_user in admin_users:
            Notification.objects.create(
                recipient=admin_user,
                sender=request.user,
                message=f"Yêu cầu phê duyệt vai trò 'Nhà tuyển dụng' cho {request.user.username}",
                type="System",
                related_url=f"/admin/approval/",
                is_read=False
            )

        role = Role.objects.get(role_name=Role.NTD)
        user_role, created = UserRole.objects.get_or_create(
            user=request.user,
            role=role,
            defaults={'is_approved': False, 'approved_at': None, 'approved_by': None}
        )

        return Response({
            "message": message,
            "ntd_profile": NtdProfileSerializer(ntd_profile).data,
            "user": {"username": request.user.username, "email": request.user.email,
                     "active_role": request.user.active_role.role_name}
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class AdminApproveNtdProfileView(generics.GenericAPIView):
    """
    API phê duyệt yêu cầu Nhà tuyển dụng.
    """
    permission_classes = [IsAdminForUserRoleApproval]

    def post(self, request, *args, **kwargs):
        ntd_profile_id = request.data.get('ntd_profile_id')
        if not ntd_profile_id:
            return Response({"detail": "ID hồ sơ nhà tuyển dụng không được cung cấp."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ntd_profile = NtdProfile.objects.get(user_id=ntd_profile_id)
        except NtdProfile.DoesNotExist:
            return Response({"detail": "Nhà tuyển dụng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        ntd_profile.is_approved = True
        ntd_profile.save()

        role, created = Role.objects.get_or_create(role_name=Role.NTD)
        user = ntd_profile.user
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={'is_approved': True, 'approved_at': timezone.now(), 'approved_by': request.user}
        )

        if not created:
            if not user_role.is_approved:
                user_role.is_approved = True
                user_role.approved_at = timezone.now()
                user_role.approved_by = request.user
                user_role.save()

        user.active_role = role
        user.save()

        Notification.objects.create(
            recipient=user,
            sender=request.user,
            message=f"Chúc mừng! Bạn đã được phê duyệt trở thành Nhà tuyển dụng.",
            type="System",
            related_url="/user/dashboard",
            is_read=False
        )

        Notification.objects.create(
            recipient=request.user,
            sender=request.user,
            message=f"Bạn đã phê duyệt yêu cầu trở thành Nhà tuyển dụng của {user.username}.",
            type="System",
            related_url=f"/admin/ntd-profile/",
            is_read=False
        )

        return Response({
            "message": "Yêu cầu phê duyệt đã được chấp nhận. Người dùng đã trở thành Nhà tuyển dụng.",
            "user": {"username": user.username, "active_role": user.active_role.role_name}
        }, status=status.HTTP_200_OK)


class AdminAssignAdminRoleView(generics.GenericAPIView):
    """
    API để admin chỉ định người dùng trở thành Quản trị viên.
    """
    permission_classes = [IsAdminForUserRoleApproval]

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Người dùng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        if user.active_role and user.active_role.role_name == Role.ADMIN:
            return Response({"detail": "Người dùng đã có vai trò Quản trị viên."}, status=status.HTTP_400_BAD_REQUEST)

        role = Role.objects.get(role_name=Role.ADMIN)

        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={'is_approved': True, 'approved_at': timezone.now(), 'approved_by': request.user}
        )

        if not created:
            user_role.is_approved = True
            user_role.approved_at = timezone.now()
            user_role.approved_by = request.user
            user_role.save()

        user.active_role = role
        user.save()

        user_serializer = UserSerializer(user)

        return Response({
            "message": "Người dùng đã được chỉ định làm Quản trị viên.",
            "user": user_serializer.data
        }, status=status.HTTP_200_OK)


class UserRolesView(generics.ListAPIView):
    """
    API để người dùng xem tất cả các vai trò của mình.
    """
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserRole.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Danh sách vai trò của bạn",
            "roles": serializer.data
        })


class ChangeRoleView(generics.UpdateAPIView):
    """
    API cho phép người dùng tự thay đổi vai trò của mình.
    Chỉ cho phép thay đổi vai trò nếu người dùng có vai trò đó trong bảng UserRole.
    """
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        new_role_name = request.data.get('role_name')

        try:
            new_role = Role.objects.get(role_name=new_role_name)
        except Role.DoesNotExist:
            return Response({"detail": "Vai trò không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if not UserRole.objects.filter(user=user, role=new_role).exists():
            return Response({"detail": "Bạn không có quyền thay đổi sang vai trò này."},
                            status=status.HTTP_400_BAD_REQUEST)

        user_role, created = UserRole.objects.get_or_create(user=user, role=new_role)

        if not created:
            user_role.role = new_role
            user_role.save()

        return Response({
            "message": f"Vai trò của bạn đã được thay đổi thành {new_role.role_name}.",
            "user": {
                "username": user.username,
                "role": user_role.role.role_name
            }
        }, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveAPIView):
    """
    API để lấy thông tin người dùng hiện tại.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UpdateUserProfileView(generics.UpdateAPIView):
    """
    API để cập nhật thông tin người dùng (name, avatar).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Cập nhật thông tin thành công.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CVViewSet(viewsets.ModelViewSet):
    """
    API để tạo, xem và xóa CV của người tìm việc.
    Chỉ chủ sở hữu mới có thể sửa CV của mình.
    Admin chỉ có thể xem và xóa CV, không thể sửa.
    """
    queryset = CV.objects.all()
    serializer_class = CVSerializer
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã đăng nhập

    def get_queryset(self):
        """
        Lấy CV của người tìm việc đã đăng nhập hoặc nếu admin thì lấy tất cả CV.
        """
        user = self.request.user
        if IsAdmin().has_permission(self.request, self):
            return CV.objects.all()  # Admin có thể xem tất cả CV
        else:
            return CV.objects.filter(ntv_profile__user=user)  # Người tìm việc chỉ xem CV của mình

    def perform_create(self, serializer):
        """
        Tạo CV cho người tìm việc nếu họ có hồ sơ NTV và role là NTV.
        Nếu người tìm việc chưa có hồ sơ, trả về thông báo lỗi.
        """
        user = self.request.user

        # Kiểm tra xem người dùng có role là NTV và đã có hồ sơ NTV
        if IsJobSeeker().has_permission(self.request, self):
            ntv_profile = user.ntv_profile  # Kiểm tra xem người dùng có hồ sơ NTV không
            if not ntv_profile:
                return Response(
                    {"detail": "Bạn chưa có hồ sơ NTV. Vui lòng tạo hồ sơ trước khi tạo CV."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Gán `ntv_profile` cho CV và lưu
            serializer.save(ntv_profile=ntv_profile)
            return Response({
                "message": "Tạo CV thành công!",
                "cv": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({"detail": "Chỉ người tìm việc (NTV) mới có thể tạo CV."}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        """
        Cập nhật CV, chỉ cho phép chủ sở hữu chỉnh sửa CV của mình.
        Admin không thể sửa CV, chỉ có thể xem và xóa.
        """
        user = self.request.user
        instance = self.get_object()  # Lấy đối tượng CV cần cập nhật

        # Kiểm tra quyền sở hữu CV
        if IsUserOwnerCV().has_object_permission(self.request, self, instance):
            serializer.save()  # Nếu là chủ sở hữu, cho phép cập nhật
            return Response({
                "message": "Cập nhật CV thành công!",
                "cv": serializer.data
            }, status=status.HTTP_200_OK)

        # Admin không được phép sửa CV, chỉ có thể xem và xóa
        if IsAdmin().has_permission(self.request, self):
            return Response({"detail": "Admin không có quyền sửa CV, chỉ có thể xem và xóa."},
                            status=status.HTTP_403_FORBIDDEN)

        return Response({"detail": "Bạn không có quyền chỉnh sửa CV của người khác."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        # Gọi phương thức xóa và sau đó trả về thông điệp thành công
        self.perform_destroy(instance)
        return Response({"message": "CV đã được xóa thành công!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsUserOwnerCV])
    def set_default(self, request, pk=None):
        """
        Chọn CV làm mặc định cho người tìm việc.
        """
        cv = self.get_object()  # Lấy CV từ request

        # Kiểm tra xem người dùng có quyền sở hữu CV này không
        if cv.ntv_profile.user != request.user:
            return Response({"detail": "Bạn không có quyền chỉnh sửa CV của người khác."},
                            status=status.HTTP_403_FORBIDDEN)

        # Cập nhật CV này thành mặc định
        cv.is_default = True
        cv.save()

        # Đảm bảo rằng các CV khác của người tìm việc không phải là mặc định nữa
        CV.objects.filter(ntv_profile=cv.ntv_profile).exclude(id=cv.id).update(is_default=False)

        return Response({
            "message": "CV đã được chọn làm mặc định!",
            "cv": CVSerializer(cv).data
        }, status=status.HTTP_200_OK)


class JobPostingViewSet(viewsets.ModelViewSet):
    """
    API để tạo, xem, sửa, xóa và phê duyệt tin tuyển dụng.
    Admin có thể xem tất cả các bài đăng tuyển dụng, NTD có thể tạo và yêu cầu phê duyệt,
    NTV chỉ xem các bài đăng đã duyệt.
    """
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        """
        Định nghĩa quyền truy cập cho từng hành động.
        """
        if self.action == 'create':
            permission_classes = [IsEmployer]  # Chỉ nhà tuyển dụng mới có thể tạo bài đăng
        elif self.action == 'update':
            permission_classes = [IsEmployer]  # Chỉ nhà tuyển dụng có thể sửa bài đăng của mình
        elif self.action == 'list':
            permission_classes = [IsAuthenticated]  # Người dùng đã đăng nhập có thể xem danh sách bài đăng
        elif self.action == 'destroy':
            permission_classes = [IsAdmin]  # Admin có thể xóa bài đăng
        elif self.action == 'approve':
            permission_classes = [IsAdmin]  # Admin có thể phê duyệt tin tuyển dụng
        elif self.action == 'request_approval':
            permission_classes = [IsEmployer]  # Nhà tuyển dụng gửi yêu cầu phê duyệt
        elif self.action == 'retrieve_by_slug_or_uuid':
            permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã đăng nhập xem tin

        else:
            permission_classes = [IsAuthenticated]  # Mặc định: Chỉ cho phép người đã đăng nhập
        return [permission() for permission in permission_classes]

    def get_object(self):
        """
        Lấy đối tượng JobPosting qua ID hoặc slug, tùy thuộc vào tham số truy vấn.
        """
        slug = self.kwargs.get('slug')
        job_posting = None
        if slug:
            job_posting = JobPosting.objects.filter(slug=slug).first()
        if not job_posting:
            job_posting = super().get_object()
        return job_posting

    def get_queryset(self):
        """
        Lấy tin tuyển dụng của người dùng đã đăng nhập.
        NTD chỉ có thể xem tin của chính mình.
        Admin có thể xem tất cả tin tuyển dụng.
        NTV chỉ có thể xem tin đã duyệt và active.
        """
        user = self.request.user

        if IsAdmin().has_permission(self.request, self):
            return JobPosting.objects.all()  # Admin có thể xem tất cả tin tuyển dụng
        elif IsEmployer().has_permission(self.request, self):
            # NTD chỉ xem tin tuyển dụng của chính mình
            return JobPosting.objects.filter(ntd_profile__user=user)
        elif IsJobSeeker().has_permission(self.request, self):
            # NTV chỉ xem các tin đã duyệt và active
            return JobPosting.objects.filter(status='approved', is_active=True)
        return JobPosting.objects.none()  # Trả về queryset trống nếu không có quyền

    def perform_create(self, serializer):
        """
        Tạo tin tuyển dụng cho người dùng đã đăng nhập.
        Gán tin tuyển dụng cho hồ sơ nhà tuyển dụng của người dùng.
        """
        user = self.request.user

        # Kiểm tra người dùng có hồ sơ nhà tuyển dụng chưa
        if not user.ntd_profile:
            raise serializers.ValidationError("Bạn cần tạo hồ sơ nhà tuyển dụng trước khi đăng tin tuyển dụng.")

        # Tạo tin tuyển dụng và gán cho hồ sơ nhà tuyển dụng của người dùng
        job_posting = serializer.save(ntd_profile=user.ntd_profile)

        return Response({
            "message": "Tạo tin tuyển dụng thành công!",
            "job_posting": JobPostingSerializer(job_posting).data
        }, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        """
        Cập nhật tin tuyển dụng.
        Chỉ nhà tuyển dụng có thể sửa tin tuyển dụng của mình.
        """
        job_posting = self.get_object()
        if job_posting.ntd_profile.user != self.request.user:
            return Response({"detail": "Bạn không có quyền sửa tin tuyển dụng này."}, status=status.HTTP_403_FORBIDDEN)

        serializer.save()
        return Response({
            "message": "Cập nhật tin tuyển dụng thành công.",
            "job_posting": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Xóa tin tuyển dụng.
        Admin có quyền xóa tất cả tin tuyển dụng, nhưng không được xóa tin đã phê duyệt.
        """
        job_posting = self.get_object()
        if job_posting.status == "approved":
            return Response({"detail": "Không thể xóa tin tuyển dụng đã được phê duyệt."},
                            status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(request, job_posting)
        job_posting.delete()

        return Response({"message": "Tin tuyển dụng đã được xóa thành công."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def approve(self, request, slug=None):
        """
        Admin phê duyệt tin tuyển dụng của nhà tuyển dụng theo slug.
        """
        # Lấy đối tượng JobPosting qua slug
        job_posting = JobPosting.objects.filter(slug=slug).first()

        if not job_posting:
            return Response({"detail": "Tin tuyển dụng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra nếu trạng thái của bài đăng không phải là 'pending_approval'
        if job_posting.status != 'pending_approval':
            return Response({"detail": "Tin tuyển dụng không cần phê duyệt."}, status=status.HTTP_400_BAD_REQUEST)

        # Cập nhật trạng thái của tin tuyển dụng thành 'approved'
        job_posting.status = 'approved'
        job_posting.save()

        # Tạo thông báo cho admin khi yêu cầu phê duyệt đã được gửi
        Notification.objects.create(
            recipient=request.user,
            sender=request.user,
            message=f"Yêu cầu phê duyệt tin tuyển dụng '{job_posting.title}' của {job_posting.ntd_profile.company_name} đã được phê duyệt.",
            type="System",
            related_url=f"/admin/job-posting/{job_posting.id}",
            is_read=False
        )

        return Response({
            "message": "Tin tuyển dụng đã được phê duyệt.",
            "job_posting": JobPostingSerializer(job_posting).data
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'])
    def request_approval(self, request, slug=None):
        """
        Nhà tuyển dụng gửi yêu cầu phê duyệt cho admin.
        """
        # Lấy đối tượng JobPosting qua slug thay vì pk
        job_posting = JobPosting.objects.filter(slug=slug).first()

        # Kiểm tra nếu không tìm thấy bài đăng
        if not job_posting:
            return Response({"detail": "Tin tuyển dụng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra trạng thái tin tuyển dụng
        if job_posting.status != 'draft':
            return Response({"detail": "Chỉ tin tuyển dụng ở trạng thái nháp mới có thể gửi yêu cầu phê duyệt."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Cập nhật trạng thái của tin tuyển dụng thành "pending_approval" (chờ phê duyệt)
        job_posting.status = 'pending_approval'
        job_posting.save()

        # Tạo thông báo cho admin
        admin_users = User.objects.filter(active_role__role_name='ADMIN')
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                sender=request.user,
                message=f"Yêu cầu phê duyệt tin tuyển dụng '{job_posting.title}' của {job_posting.ntd_profile.company_name}.",
                type="System",
                related_url=f"/admin/job-posting/{job_posting.id}",
                is_read=False
            )

        return Response({"message": "Yêu cầu phê duyệt đã được gửi."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def retrieve_by_slug_or_uuid(self, request, *args, **kwargs):
        """
        Lấy chi tiết tin tuyển dụng theo slug hoặc uuid.
        """
        identifier = kwargs.get('slug')  # Lấy slug hoặc uuid từ URL
        print(identifier)
        # Kiểm tra nếu là slug
        if '-' in identifier:  # Nếu là slug
            try:
                job_posting = JobPosting.objects.get(slug=identifier)
            except JobPosting.DoesNotExist:
                return Response({"detail": "Tin tuyển dụng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
        else:  # Nếu không có dấu gạch ngang, coi là uuid
            try:
                job_posting = JobPosting.objects.get(id=identifier)
            except JobPosting.DoesNotExist:
                return Response({"detail": "Tin tuyển dụng không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra quyền xem bài đăng dựa trên trạng thái và vai trò người dùng
        if IsJobSeeker().has_permission(self.request, self):
            if job_posting.status != 'approved':  # Người tìm việc chỉ có thể xem tin đã phê duyệt
                return Response({"detail": "Bạn không có quyền xem bài đăng này."}, status=status.HTTP_403_FORBIDDEN)

        if IsEmployer().has_permission(self.request, self):
            if job_posting.ntd_profile.user != self.request.user:  # Nhà tuyển dụng chỉ xem tin của mình
                return Response({"detail": "Bạn không có quyền xem bài đăng này."}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "job_posting": JobPostingSerializer(job_posting).data
        }, status=status.HTTP_200_OK)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Ứng viên (NTV) sẽ gửi hồ sơ ứng tuyển vào công việc.
        """
        job_posting = JobPosting.objects.get(id=self.request.data.get('job_posting'))
        if job_posting.status != 'approved':
            return Response({"detail": "Công việc này chưa được phê duyệt."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(user=self.request.user)

        return Response({
            "message": "Ứng tuyển thành công.",
            "application": serializer.data
        }, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        """
        Lấy danh sách các ứng tuyển của người dùng đã đăng nhập.
        """
        return Application.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        NTD có thể duyệt, từ chối hoặc mời phỏng vấn ứng viên.
        """
        application = self.get_object()
        status = request.data.get('status')

        if status not in dict(Application.STATUS_CHOICES):
            return Response({"detail": "Trạng thái không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        application.status = status
        application.save()

        return Response({
            "message": f"Trạng thái ứng tuyển đã được cập nhật thành {status}.",
            "application": ApplicationSerializer(application).data
        }, status=status.HTTP_200_OK)


class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.all()
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Định nghĩa quyền truy cập cho từng hành động.
        """
        permission_classes = []  # Initialize permission_classes with an empty list

        if self.action == 'schedule_interview':
            # Chỉ NTD có thể mời phỏng vấn
            permission_classes = [IsEmployer]
        elif self.action == 'update_result':
            # Chỉ NTD có thể cập nhật kết quả phỏng vấn
            permission_classes = [IsEmployer]
        elif self.action == 'list':
            # Tất cả người dùng đã đăng nhập có thể xem danh sách phỏng vấn
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'])
    def schedule_interview(self, request):
        """
        NTD có thể mời ứng viên phỏng vấn.
        Nhận application_id và scheduled_time, tự động tạo cuộc phỏng vấn và trả về thông tin.
        """
        application_id = request.data.get('application_id')
        scheduled_time = request.data.get('scheduled_time')

        # Lấy đối tượng Application (đơn ứng tuyển)
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return Response({"detail": "Đơn ứng tuyển không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Tạo Jitsi meeting link using a unique meeting ID (UUID)
        meeting_id = uuid.uuid4()  # Tạo ID cuộc họp duy nhất
        jitsi_url = f"https://meet.jit.si/{meeting_id}"  # Tạo liên kết Jitsi

        # Tạo cuộc phỏng vấn và lưu vào cơ sở dữ liệu
        interview = Interview.objects.create(
            application=application,
            scheduled_time=scheduled_time,
            platform_link=jitsi_url
        )

        # Gửi thông báo đến người tìm việc về lịch phỏng vấn
        Notification.objects.create(
            recipient=application.user,
            sender=request.user,
            message=f"Cuộc phỏng vấn cho công việc '{application.job_posting.title}' đã được lên lịch vào {scheduled_time}.",
            type="InterviewReminder",
            related_url=f"/interviews/{interview.id}/",
            is_read=False
        )

        return Response({
            "message": "Lịch phỏng vấn đã được lên lịch thành công.",
            "interview": InterviewSerializer(interview).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def update_result(self, request):
        """
        Cập nhật kết quả phỏng vấn.
        Nhận interview_id, kết quả phỏng vấn (Passed, Failed, Pending) và notes (tùy chọn) từ request body.
        """
        interview_id = request.data.get('interview_id')
        result = request.data.get('result')
        notes_ntd = request.data.get('notes_ntd')

        if not interview_id:
            return Response({"detail": "Vui lòng cung cấp interview_id."}, status=status.HTTP_400_BAD_REQUEST)

        if result not in ['Passed', 'Failed', 'Pending']:
            return Response({"detail": "Kết quả không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interview = Interview.objects.get(id=interview_id)
        except Interview.DoesNotExist:
            return Response({"detail": "Cuộc phỏng vấn không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        interview.result = result
        interview.status = 'Completed'
        if notes_ntd is not None:
            interview.notes_ntd = notes_ntd
        interview.save()

        Notification.objects.create(
            recipient=interview.application.user,
            sender=request.user,
            message=f"Phỏng vấn cho công việc '{interview.application.job_posting.title}' đã được chấm điểm. Kết quả: {result}.",
            type="StatusUpdate",
            related_url=f"/interviews/{interview.id}/",
            is_read=False
        )

        return Response({
            "message": f"Kết quả phỏng vấn đã được cập nhật thành {result}.",
            "interview": InterviewSerializer(interview).data
        }, status=status.HTTP_200_OK)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Trả về tất cả các tin nhắn của người dùng hiện tại (dù là người gửi hoặc người nhận).
        """
        user = self.request.user
        return Message.objects.filter(sender=user) | Message.objects.filter(recipient=user)

    def perform_create(self, serializer):
        """
        Tạo một tin nhắn mới, tự động gán người gửi từ request.user và đảm bảo recipient tồn tại.
        Gửi tin nhắn lên Firebase Realtime Database với ID từ DB.
        """
        recipient = self.request.data.get('recipient')

        # Kiểm tra recipient có hợp lệ không
        if not recipient:
            raise ValidationError("Recipient is required.")

        if recipient == self.request.user.id:
            raise ValidationError("Sender and recipient cannot be the same.")

        # Gán người gửi là người dùng hiện tại
        message = serializer.save(sender=self.request.user)
        print(message.sender.id, message.recipient.id)
        # Dữ liệu tin nhắn cần lưu vào Firebase
        message_data = {
            "sender": message.sender.id,
            "recipient": message.recipient.id,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "is_read": message.is_read,
            "read_at": message.read_at.isoformat() if message.read_at else None,  # Thêm trường 'read_at'
        }

        # Lưu tin nhắn vào Firebase (dưới node 'messages') với ID từ DB
        ref = db.reference(f'messages/{message.id}')  # Sử dụng ID tin nhắn từ DB
        ref.set(message_data)  # Lưu tin nhắn vào Firebase với ID từ DB

    def update(self, request, *args, **kwargs):
        """
        Cập nhật trạng thái tin nhắn khi người nhận đọc tin nhắn.
        """
        message = self.get_object()

        # Chỉ cho phép người nhận đánh dấu tin nhắn là đã đọc
        if message.recipient != request.user:
            return Response({"detail": "You cannot update this message."}, status=status.HTTP_403_FORBIDDEN)

        # Đánh dấu tin nhắn là đã đọc
        message.is_read = True
        message.read_at = timezone.now()  # Cập nhật 'read_at' với thời gian hiện tại
        message.save()

        # Cập nhật trạng thái tin nhắn trong Firebase
        message_ref = db.reference(f'messages/{message.id}')
        message_ref.update({
            "is_read": True,
            "read_at": message.read_at.isoformat()  # Cập nhật 'read_at' trong Firebase
        })

        return Response(MessageSerializer(message).data)

    def destroy(self, request, *args, **kwargs):
        """
        Xóa tin nhắn nếu người dùng là người gửi hoặc người nhận.
        """
        message = self.get_object()

        # Kiểm tra xem người yêu cầu xóa có phải là người gửi hoặc người nhận không
        if message.sender != request.user and message.recipient != request.user:
            return Response({"detail": "You cannot delete this message."}, status=status.HTTP_403_FORBIDDEN)

        # Xóa tin nhắn trong cơ sở dữ liệu
        message.delete()

        # Xóa tin nhắn từ Firebase
        message_ref = db.reference(f'messages/{message.id}')
        message_ref.delete()

        return Response({"detail": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class AllConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Truy xuất tất cả các tin nhắn từ Firebase
        ref = db.reference('messages')  # Truy xuất đến node 'messages'
        messages_data = ref.order_by_child('created_at').get()  # Lấy tin nhắn sắp xếp theo thời gian

        # Lọc các cuộc hội thoại theo người dùng hiện tại
        conversations = {}
        for message_id, message in messages_data.items():
            sender_id = message['sender']
            recipient_id = message['recipient']

            # Chỉ lấy tin nhắn có liên quan đến người dùng hiện tại (người gửi hoặc người nhận)
            if sender_id == user.id or recipient_id == user.id:
                # Tạo một khóa cuộc hội thoại duy nhất dựa trên cặp người gửi và người nhận
                participant_id = recipient_id if sender_id == user.id else sender_id

                # Nếu cuộc hội thoại chưa tồn tại, tạo mới
                if participant_id not in conversations:
                    conversations[participant_id] = {
                        'participant': participant_id,
                        'messages': []
                    }

                # Kiểm tra sự tồn tại của trường 'read_at', nếu không có thì gán là null
                read_at = message.get('read_at', None)  # Sử dụng `.get()` để tránh KeyError

                # Thêm tin nhắn vào cuộc hội thoại
                conversations[participant_id]['messages'].append({
                    'id': message_id,
                    'sender': sender_id,
                    'recipient': recipient_id,
                    'content': message['content'],
                    'created_at': message['created_at'],
                    'is_read': message['is_read'],
                    'read_at': read_at  # Trường 'read_at' có thể là None nếu chưa được gán
                })

        # Chuyển dữ liệu cuộc hội thoại thành dạng chuẩn để trả về
        conversation_list = []
        for participant_id, conversation in conversations.items():
            participant = User.objects.get(id=participant_id)  # Lấy thông tin người tham gia (người đối diện)
            conversation_data = {
                'participant': participant.username,  # Hoặc bạn có thể trả về thông tin khác của người tham gia
                'messages': conversation['messages'],
            }
            conversation_list.append(conversation_data)

        return Response(conversation_list)