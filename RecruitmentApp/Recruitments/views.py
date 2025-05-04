from django.http import HttpResponse
from django.shortcuts import render
import datetime
import uuid

from Recruitments import paginators
from rest_framework import viewsets, status, serializers, parsers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes

from .models import Message
from .serializers import MessageSerializer, UserSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from . import firebase_config
from django.db import models

from django.contrib.auth import get_user_model
from .models import Role, UserRole, NtvProfile, NtdProfile, JobPosting, CV, Application, Interview, Notification
from .serializers import (
    RegistrationSerializer,
    NtdRequestSerializer,
    ApproveNtdRequestSerializer,
    NtvProfileSerializer,
    ChangeActiveRoleSerializer,
    JobPostingSerializer,
    ApproveJobPostingSerializer,
    CVSeralizer,
    ApplicationSerializer,
    InterviewSerializer,
    NotificationSerializer, NtdProfileSerializer
)
from .permissions import (
    RegisterUserPermission,
    BecomeNtdPermission,
    ApproveNtdRolePermission,
    BecomeNtvPermission,
    SwitchActiveRolePermission,
    JobPostingPermission,
    CvPermission,
    ApplicationPermission,
    InterviewPermission,
    NotificationPermission,
)

User = get_user_model()


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [RegisterUserPermission]
    http_method_names = ['post']


class BecomeNtdViewSet(viewsets.ViewSet):
    permission_classes = [BecomeNtdPermission]
    serializer_class = NtdRequestSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveNtdRequestViewSet(viewsets.ViewSet):
    permission_classes = [ApproveNtdRolePermission]
    serializer_class = ApproveNtdRequestSerializer
    http_method_names = ['post']

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                user_id = serializer.validated_data['user_id']
                try:
                    ntd_role = Role.objects.get(roleName='NTD')
                    user_role = UserRole.objects.get(user_id=user_id, role=ntd_role)
                except UserRole.DoesNotExist:
                    return Response({'error': 'Không tìm thấy yêu cầu phê duyệt cho người dùng này.'}, status=status.HTTP_404_NOT_FOUND)
                except Role.DoesNotExist:
                    return Response({'error': 'Vai trò NTD không tồn tại.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                updated_user_role = serializer.update(user_role, serializer.validated_data)
                if updated_user_role.isApproved:
                    user = User.objects.get(id=user_id)
                    message = "Chúc mừng! Yêu cầu trở thành Nhà tuyển dụng của bạn đã được phê duyệt. Bạn có thể bắt đầu tạo hồ sơ công ty và đăng tin tuyển dụng."
                    Notification.objects.create(recipient=user, message=message, type='StatusUpdate')
                return Response(ApproveNtdRequestSerializer(updated_user_role).data, status=status.HTTP_200_OK)
            except serializers.ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NtdProfileViewSet(viewsets.ModelViewSet):
    serializer_class = NtdProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NtdProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class NtvProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [BecomeNtvPermission, IsAuthenticated]
    serializer_class = NtvProfileSerializer
    http_method_names = ['get', 'post', 'put', 'patch']
    # parser_classes = [parsers.MultiPartParser] # Dùng để lấy tập tin

    def get_queryset(self):
        return NtvProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ChangeActiveRoleViewSet(viewsets.ViewSet):
    permission_classes = [SwitchActiveRolePermission]
    serializer_class = ChangeActiveRoleSerializer
    http_method_names = ['post']

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_role_name = serializer.validated_data['activeRole']
            try:
                role = Role.objects.get(roleName=new_role_name)
                if UserRole.objects.filter(user=user, role=role,
                                           isApproved=True).exists() or role.roleName == 'NTV' and UserRole.objects.filter(
                    user=user, role=role).exists():
                    old_role = user.activeRole
                    user.activeRole = role
                    user.save()
                    # Tạo thông báo khi thay đổi vai trò hoạt động
                    message = f"Vai trò hoạt động của bạn đã được chuyển thành '{role.get_roleName_display()}'."
                    Notification.objects.create(recipient=user, message=message, type='StatusUpdate')
                    return Response(ChangeActiveRoleSerializer(user).data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': f"Bạn chưa được cấp quyền hoặc chưa kích hoạt vai trò '{new_role_name}'."},
                        status=status.HTTP_400_BAD_REQUEST)
            except Role.DoesNotExist:
                return Response({'error': f"Vai trò '{new_role_name}' không tồn tại."},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.filter(isActive=True)
    serializer_class = JobPostingSerializer
    permission_classes = [JobPostingPermission]

    def get_queryset(self):
        if self.request.user.is_staff:
            return JobPosting.objects.all()
        elif hasattr(self.request.user,
                     'ntdprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTD':
            return JobPosting.objects.filter(ntd_profile__user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        try:
            ntd_profile = NtdProfile.objects.get(user=self.request.user)
            serializer.save(ntd_profile=ntd_profile)
        except NtdProfile.DoesNotExist:
            return Response({'error': 'Bạn cần tạo hồ sơ Nhà tuyển dụng trước khi đăng tin tuyển dụng.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        job_posting = self.get_object()
        serializer = ApproveJobPostingSerializer(job_posting, data={'isActive': True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        job_posting = self.get_object()
        serializer = ApproveJobPostingSerializer(job_posting, data={'isActive': False}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CVViewSet(viewsets.ModelViewSet):
    serializer_class = CVSeralizer
    permission_classes = [CvPermission]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CV.objects.all()
        elif hasattr(self.request.user,
                     'ntvprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTV':
            return CV.objects.filter(ntv_profile__user=self.request.user)
        return CV.objects.none()

    def perform_create(self, serializer):
        try:
            ntv_profile = NtvProfile.objects.get(user=self.request.user)
            serializer.save(ntv_profile=ntv_profile)
        except NtvProfile.DoesNotExist:
            return Response({'error': 'Bạn cần tạo hồ sơ Người tìm việc trước khi tạo CV.'},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [ApplicationPermission]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Application.objects.all()
        elif hasattr(self.request.user,
                     'ntdprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTD':
            ntd_profile = self.request.user.ntdprofile
            return Application.objects.filter(job_posting__ntd_profile=ntd_profile)
        elif hasattr(self.request.user,
                     'ntvprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTV':
            return Application.objects.filter(user=self.request.user)
        return Application.objects.none()

    def retrieve(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(application)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            if (hasattr(request.user, 'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD' and application.job_posting.ntd_profile == request.user.ntdprofile) or request.user == application.user:
                old_status = application.status
                serializer.save()
                new_status = application.status
                if old_status != new_status:
                    message = f"Trạng thái ứng tuyển của bạn cho vị trí '{application.job_posting.title}' đã được cập nhật thành '{application.get_status_display()}'."
                    Notification.objects.create(recipient=application.user, message=message, type='StatusUpdate', relatedUrl=f'/applications/{application.id}/')
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        message = f"Bạn đã ứng tuyển thành công vào vị trí '{serializer.instance.job_posting.title}'."
        Notification.objects.create(recipient=self.request.user, message=message, type='StatusUpdate', relatedUrl=f'/applications/{serializer.instance.id}/')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def withdraw(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if request.user == application.user:
            application.status = 'Withdrawn'
            application.save()
            message = f"Bạn đã rút hồ sơ ứng tuyển cho vị trí '{application.job_posting.title}'."
            Notification.objects.create(recipient=request.user, message=message, type='StatusUpdate', relatedUrl=f'/applications/{application.id}/')
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [InterviewPermission]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Interview.objects.all()
        elif hasattr(self.request.user,
                     'ntdprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTD':
            ntd_profile = self.request.user.ntdprofile
            return Interview.objects.filter(application__job_posting__ntd_profile=ntd_profile)
        elif hasattr(self.request.user,
                     'ntvprofile') and self.request.user.activeRole and self.request.user.activeRole.roleName == 'NTV':
            return Interview.objects.filter(application__user=self.request.user)
        return Interview.objects.none()

    def perform_create(self, serializer):
        interview = serializer.save()
        application = interview.application
        # Thông báo cho ứng viên và NTD khi có lịch phỏng vấn mới
        message_ntv = f"Bạn có lịch phỏng vấn mới cho vị trí '{application.job_posting.title}' vào lúc {interview.scheduledTime}."
        Notification.objects.create(recipient=application.user, message=message_ntv, type='InterviewReminder', relatedUrl=f'/interviews/{interview.id}/')
        message_ntd = f"Bạn đã lên lịch phỏng vấn cho ứng viên '{application.user.username}' vào lúc {interview.scheduledTime} cho vị trí '{application.job_posting.title}'."
        Notification.objects.create(recipient=application.job_posting.ntd_profile.user, message=message_ntd, type='InterviewReminder', relatedUrl=f'/interviews/{interview.id}/')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def evaluate(self, request, pk=None):
        try:
            interview = Interview.objects.get(pk=pk)
            application = interview.application
        except Interview.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if hasattr(request.user,
                   'ntdprofile') and request.user.activeRole and request.user.activeRole.roleName == 'NTD' and application.job_posting.ntd_profile == request.user.ntdprofile:
            result = request.data.get('result')
            if result == 'Passed':
                application.status = 'Offered'
                message = f"Chúc mừng! Bạn đã được mời nhận việc cho vị trí '{application.job_posting.title}'."
                Notification.objects.create(recipient=application.user, message=message, type='StatusUpdate', relatedUrl=f'/applications/{application.id}/')
            elif result == 'Failed':
                application.status = 'Rejected'
                message = f"Rất tiếc, hồ sơ ứng tuyển của bạn cho vị trí '{application.job_posting.title}' không phù hợp."
                Notification.objects.create(recipient=application.user, message=message, type='StatusUpdate', relatedUrl=f'/applications/{application.id}/')
            application.result = result
            application.save()

            # Cập nhật trường result của Interview
            interview.result = result
            interview.notesNtd = request.data.get('notesNtd')
            interview.save()

            serializer = self.get_serializer(interview)  # Serialize interview để trả về
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        other_user_id = self.request.query_params.get('user_id')
        if other_user_id:
            try:
                other_user = get_object_or_404(User, id=other_user_id)  # Sử dụng model User tùy chỉnh
                conversation = Conversation.objects.filter(participants=self.request.user).filter(participants=other_user).first()
                if conversation:
                    return Message.objects.filter(conversation=conversation).order_by('timestamp')
                return Message.objects.none()
            except ValueError:
                return Message.objects.none()
        return Message.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create_with_firebase(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create_with_firebase(self, serializer):
        try:
            message = serializer.save(sender=self.request.user)
            self.send_to_firebase(message)
            # Tự động tạo thông báo cho người nhận tin nhắn
            recipient = message.recipient
            if recipient != self.request.user:
                notification_message = f"Bạn có tin nhắn mới từ {self.request.user.username}."
                Notification.objects.create(recipient=recipient, message=notification_message, type='ChatMessage', relatedUrl=f'/conversations/{message.conversation.id}/')
        except Exception as e:
            print(f"Lỗi khi lưu tin nhắn và gửi lên Firebase: {e}")
            raise

    @staticmethod
    def send_to_firebase(message):
        """Gửi thông tin tin nhắn lên Firebase Realtime Database."""
        try:
            ref = firebase_config.db.reference(f'messages/{message.conversation.id}/{message.recipient.id}/{message.id}')
            ref.set({
                'sender_id': message.sender.id,
                'recipient_id': message.recipient.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'isRead': False
            })
            print(f"Đã gửi tin nhắn ID {message.id} lên Firebase.")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn ID {message.id} lên Firebase: {e}")


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_list(request):
    """Lấy danh sách tất cả người dùng."""
    users = User.objects.exclude(id=request.user.id)  # Sử dụng model User tùy chỉnh
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet cho phép xem và quản lý thông báo của người dùng.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Trả về danh sách tất cả thông báo của người dùng hiện tại,
        sắp xếp theo thời gian tạo mới nhất.
        """
        return Notification.objects.filter(recipient=self.request.user).order_by('-createdAt')

    def perform_create(self, serializer):
        """
        Tạo một thông báo mới và tự động gán người nhận là người dùng hiện tại.
        """
        serializer.save(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Đánh dấu một thông báo là đã đọc.
        """
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.isRead = True
            notification.save()
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    return render(request, template_name='index.html', context= {
        'name':'NguyenTanLoc'
    })