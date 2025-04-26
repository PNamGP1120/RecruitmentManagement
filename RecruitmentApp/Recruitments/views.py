from datetime import timedelta

from rest_framework import viewsets, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .permissions import IsAdminUser, IsNTVUser, IsNTDUser, IsApprovedNTDUser
from .serializers import RegistrationSerializer, LoginSerializer, NtdRequestSerializer, ApproveNtdRequestSerializer, \
    CVSerializer, NtvProfileSerializer, UserAndNtvProfileUpdateSerializer, UserUpdateSerializer, JobPostingSerializer, \
    NtdProfileSerializer, ApplicationSerializer
from oauth2_provider.models import Application, AccessToken, RefreshToken
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from django.utils import timezone
from django.conf import settings
from .models import UserRole, Role, CV, NtvProfile, JobPosting, NtdProfile


class RegistrationViewSet(viewsets.ViewSet):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Tự động tạo NtdProfile
            NtdProfile.objects.create(user=user)

            # Tự động gửi yêu cầu phê duyệt vai trò NTD
            ntd_role = Role.objects.get(roleName='NTD')
            UserRole.objects.create(user=user, role=ntd_role, isApproved=False)

            refresh = JWTRefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'message': 'Đăng ký thành công. Bạn đã có thể tạo hồ sơ Nhà tuyển dụng.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Tạo access token OAuth2 (client credentials grant)
            try:
                application = Application.objects.get(
                    client_type=Application.CLIENT_CONFIDENTIAL,
                    authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS
                )
                token = AccessToken.objects.create(
                    user=user,
                    token=get_random_string(30),
                    application=application,
                    scope='read write',
                    expires=timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'])
                )
                refresh_token = RefreshToken.objects.create(
                    user=user,
                    token=get_random_string(30),
                    application=application,
                    access_token=token,
                    # 'expires' parameter was removed
                )

                # Tạo access và refresh token JWT
                jwt_refresh = JWTRefreshToken.for_user(user)

                return Response({
                    'oauth2_access_token': token.token,
                    'oauth2_refresh_token': refresh_token.token,
                    'jwt_access_token': str(jwt_refresh.access_token),
                    'jwt_refresh_token': str(jwt_refresh),
                    'message': 'Đăng nhập thành công.'
                }, status=status.HTTP_200_OK)
            except Application.DoesNotExist:
                return Response({'error': 'OAuth2 Application không tồn tại.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NtdRequestViewSet(viewsets.ViewSet):
    serializer_class = NtdRequestSerializer
    permission_classes = [IsAuthenticated] # Yêu cầu người dùng đã đăng nhập

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NtdProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho API quản lý hồ sơ Nhà tuyển dụng.
    """
    serializer_class = NtdProfileSerializer
    permission_classes = [IsAuthenticated] # Chỉ cần người dùng đã đăng nhập
    queryset = NtdProfile.objects.all()

    def get_queryset(self):
        return NtdProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

class ApproveNtdRequestViewSet(viewsets.ViewSet):
    serializer_class = ApproveNtdRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def update(self, request, pk=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user_role = get_object_or_404(
                UserRole,
                user_id=serializer.validated_data['user_id'],
                role__roleName=Role.NTD,
                isApproved=False # Chỉ phê duyệt các yêu cầu chưa được duyệt
            )
            approved_user_role = serializer.update(user_role, serializer.validated_data)
            return Response({'message': f'Đã phê duyệt yêu cầu trở thành Nhà tuyển dụng cho người dùng ID {approved_user_role.user_id}.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CVViewSet(viewsets.ModelViewSet):
    serializer_class = CVSerializer
    permission_classes = [IsAuthenticated, IsNTVUser]
    queryset = CV.objects.all() # Để Django biết cách truy vấn các đối tượng CV

    def get_queryset(self):
        # Chỉ trả về CV của người dùng đang gửi request
        return CV.objects.filter(ntv_profile__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(ntv_profile=self.request.user.ntv_profile)

class UserAccountUpdateViewSet(viewsets.ViewSet):
    """
    ViewSet để người dùng đã đăng nhập cập nhật thông tin tài khoản của họ.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, pk = None):
        user = request.user
        serializer = self.serializer_class(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # *** CHÚ Ý: Chúng ta cần thêm logic kích hoạt role NTV ở đây ***
            ntv_role = Role.objects.get(roleName='NTV')
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=ntv_role,
                defaults={'isApproved': True, 'approvedAt': timezone.now()}
            )
            user.activeRole = ntv_role
            user.save()
            return Response({'message': 'Cập nhật tài khoản thành công và đã kích hoạt vai trò Người tìm việc.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NtvProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet để người dùng đã đăng nhập tạo và cập nhật hồ sơ Người tìm việc,
    đồng thời kích hoạt vai trò NTV.
    """
    serializer_class = NtvProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NtvProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

# class NtvProfileViewSet(viewsets.ModelViewSet):
#     serializer_class = NtvProfileSerializer
#     permission_classes = [IsAuthenticated]  # Chỉ người dùng đã đăng nhập mới có thể tạo/cập nhật
#
#     def get_queryset(self):
#         return NtvProfile.objects.filter(user=self.request.user)
#
#     def get_object(self):
#         """Chỉ cho phép truy cập vào hồ sơ của chính người dùng."""
#         queryset = self.filter_queryset(self.get_queryset())
#         obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
#         return obj
#
#     def perform_create(self, serializer):
#         if NtvProfile.objects.filter(user=self.request.user).exists():
#             return Response({'error': 'Bạn đã có hồ sơ Người tìm việc.'}, status=status.HTTP_400_BAD_REQUEST)
#         serializer.save(user=self.request.user)
#         self.activate_ntv_role(self.request.user)
#
#     def perform_update(self, serializer):
#         serializer.save()
#         self.activate_ntv_role(self.request.user)
#
#     def activate_ntv_role(self, user):
#         ntv_role = Role.objects.get(roleName='NTV')
#         user_role, created = UserRole.objects.get_or_create(
#             user=user,
#             role=ntv_role,
#             defaults={'isApproved': True, 'approvedAt': timezone.now()}
#         )
#         user.activeRole = ntv_role
#         user.save()
#
#     def create(self, request, *args, **kwargs):
#         response = self.perform_create(self.get_serializer(data=request.data))
#         if isinstance(response, Response):
#             return response
#         return Response({'message': 'Hồ sơ Người tìm việc đã được tạo và vai trò NTV đã được kích hoạt.'}, status=status.HTTP_201_CREATED)
#
#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({'message': 'Hồ sơ Người tìm việc đã được cập nhật và vai trò NTV đã được kích hoạt.'}, status=status.HTTP_200_OK)

class UserAndNtvProfileUpdateViewSet(viewsets.ViewSet):
    serializer_class = UserAndNtvProfileUpdateSerializer
    permission_classes = [IsAuthenticated] # Chỉ người dùng đã đăng nhập

    def update(self, request, pk=None):
        user = request.user
        serializer = self.serializer_class(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Cập nhật thông tin tài khoản và hồ sơ Người tìm việc thành công.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobPostingViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho API quản lý tin tuyển dụng của Nhà tuyển dụng.
    """
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated, IsNTDUser, IsApprovedNTDUser]
    queryset = JobPosting.objects.all()

    def get_queryset(self):
        # Chỉ cho phép nhà tuyển dụng xem các tin tuyển dụng của chính họ
        return JobPosting.objects.filter(ntd_profile__user=self.request.user)

    def perform_create(self, serializer):
        # Tự động gán ntd_profile cho tin tuyển dụng dựa trên người dùng đang đăng nhập
        try:
            ntd_profile = self.request.user.ntd_profile
            serializer.save(ntd_profile=ntd_profile)
        except AttributeError:
            return Response({'error': 'Bạn không có hồ sơ Nhà tuyển dụng.'}, status=status.HTTP_400_BAD_REQUEST)

class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho API ứng tuyển của Người tìm việc.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsNTVUser]
    queryset = Application.objects.all()

    def get_queryset(self):
        # Chỉ trả về các ứng tuyển của người dùng đang gửi request
        return Application.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Chúng ta có thể không muốn cho phép update hoặc delete ứng tuyển qua API,
    # tùy thuộc vào yêu cầu nghiệp vụ.

    # def update(self, request, pk=None):
    #     pass

    # def destroy(self, request, pk=None):
    #     pass

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Lấy thông tin chi tiết của một ứng tuyển cụ thể của người dùng.
        """
        application = self.get_object()
        serializer = self.get_serializer(application)
        return Response(serializer.data)


