import re
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from difflib import SequenceMatcher
from django.core import validators
from firebase_admin import db as firebase_db

from . import firebase_config
from .models import NtvProfile, NtdProfile, UserRole, Notification, Role, CV, JobPosting, Application, Interview, \
    Message, User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho thông tin người dùng.
    """
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active', 'avatar', 'active_role']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.avatar.url if instance.avatar else None
        return rep


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer cho đăng ký người dùng. Không gán role ngay khi tạo tài khoản.
    """
    username = serializers.CharField(
        max_length=150,
        validators=[validators.RegexValidator(r'^[a-zA-Z0-9._-]+$', message="Chỉ cho phép chữ cái, số, dấu chấm, gạch dưới và gạch ngang.")]
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    @staticmethod
    def validate_username(value):
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError("Tên người dùng này đã tồn tại.")
        return value

    def validate_email(self, value):
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã tồn tại.")
        return value

    def validate(self, data):
        password = data.get('password')
        if password != data['password2']:
            raise serializers.ValidationError("Mật khẩu không khớp.")

        if len(password) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")

        if not (re.search(r'[A-Z]', password) and re.search(r'\d', password) and re.search(r'[\W_]', password)):
            raise serializers.ValidationError("Mật khẩu không đủ mạnh. Phải có ít nhất 8 ký tự, một chữ cái viết hoa, một số và một ký tự đặc biệt.")

        user = get_user_model()(username=data['username'], email=data['email'])
        if password and any(SequenceMatcher(None, password.lower(), getattr(user, attr, '').lower()).quick_ratio() >= 0.7 for attr in ['username', 'email'] if getattr(user, attr, '')):
            raise serializers.ValidationError("Mật khẩu quá giống với tên người dùng hoặc email.")

        return data

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer cho đăng nhập người dùng.
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)


class NtvProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho hồ sơ người tìm việc (NTV).
    """
    class Meta:
        model = NtvProfile
        fields = ['summary', 'experience', 'education', 'skills', 'phone_number', 'date_of_birth', 'gender']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'skills':
                instance.skills.set(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class NtdProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho hồ sơ nhà tuyển dụng (NTD).
    """
    class Meta:
        model = NtdProfile
        fields = ['company_name', 'company_website', 'company_description', 'industry', 'address', 'company_logo']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        ntd_profile = NtdProfile.objects.create(**validated_data)
        return ntd_profile

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['company_logo_url'] = instance.company_logo.url if instance.company_logo else None
        return rep


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer cho vai trò người dùng.
    """
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'is_approved', 'approved_at', 'approved_by']

    @staticmethod
    def update_user_role(instance, validated_data):
        instance.is_approved = validated_data.get('is_approved', instance.is_approved)
        instance.approved_at = validated_data.get('approved_at', instance.approved_at)
        instance.approved_by = validated_data.get('approved_by', instance.approved_by)
        instance.save()
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer cho thông báo người dùng.
    """
    class Meta:
        model = Notification
        fields = ['recipient', 'sender', 'message', 'type', 'related_url', 'is_read', 'read_at']

    def create(self, validated_data):
        notification = Notification.objects.create(**validated_data)
        return notification


class BecomeAdminSerializer(serializers.ModelSerializer):
    """
    Serializer cho yêu cầu thay đổi vai trò người dùng thành admin.
    """
    class Meta:
        model = UserRole
        fields = ['user', 'role']

    def create(self, validated_data):
        role = Role.objects.get(role_name=Role.ADMIN)
        user = validated_data['user']
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            is_approved=False
        )
        return user_role


class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ['id', 'file_name', 'file_path', 'version_name', 'is_default', 'is_deleted']

    def validate(self, data):
        """
        Kiểm tra nếu CV là mặc định, chỉ có một CV mặc định được phép cho mỗi người tìm việc.
        """
        if data.get('is_default', False):
            ntv_profile = data.get('ntv_profile')
            if ntv_profile and ntv_profile.cvs.filter(is_default=True).exists():
                raise serializers.ValidationError("Chỉ được phép có một CV mặc định.")
        return data

    def update(self, instance, validated_data):
        # Nếu được yêu cầu làm CV mặc định, cập nhật các CV còn lại thành không phải mặc định
        if validated_data.get('is_default') and validated_data['is_default'] is True:
            # Đặt tất cả CV của người tìm việc thành không phải mặc định
            CV.objects.filter(ntv_profile=instance.ntv_profile).update(is_default=False)

        # Cập nhật các trường còn lại
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['file_path'] = instance.file_path.url if instance.file_path else None
        return rep


class JobPostingSerializer(serializers.ModelSerializer):
    ntd_profile = serializers.PrimaryKeyRelatedField(queryset=NtdProfile.objects.all(), required=False)

    class Meta:
        model = JobPosting
        fields = ['id', 'ntd_profile', 'title', 'slug', 'description', 'location', 'salary_min', 'salary_max', 'experience_required', 'job_type', 'status', 'expiration_date']

    def validate(self, data):
        # Nếu người dùng không phải là admin và không có ntd_profile, trả về lỗi
        if not self.context['request'].user.ntd_profile:
            raise serializers.ValidationError("Bạn cần tạo hồ sơ nhà tuyển dụng trước khi đăng tin tuyển dụng.")
        return data


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['user', 'job_posting', 'cv', 'status', 'cover_letter']
        read_only_fields = ['user']  # Không cho phép chỉnh sửa user từ ngoài

    def create(self, validated_data):
        # Tự động gán user là người dùng đã đăng nhập
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']

class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ['id', 'application', 'scheduled_time', 'platform_link', 'status', 'notes_ntd', 'notes_ntv', 'result']
        read_only_fields = ['application']


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)  # Chỉ có thể đọc (người gửi là người dùng hiện tại)
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Người nhận phải là một người dùng hợp lệ

    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'content', 'created_at', 'is_read', 'read_at']

    def validate(self, data):
        """
        Kiểm tra sự hợp lệ của dữ liệu.
        """
        # Kiểm tra recipient có hợp lệ
        if not data.get('recipient'):
            raise serializers.ValidationError("Recipient is required.")
        return data


class ConversationSerializer(serializers.Serializer):
    participant = serializers.SerializerMethodField()  # Người đối diện
    messages = MessageSerializer(many=True)  # Danh sách các tin nhắn trong cuộc hội thoại

    def get_participant(self, obj):
        """
        Lấy thông tin về người tham gia cuộc hội thoại (người đối diện).
        """
        user = self.context['request'].user  # Người dùng hiện tại

        # Nếu người gửi là người dùng hiện tại, trả về recipient là người đối diện, ngược lại trả về sender
        if obj['sender'] == user:
            return obj['recipient']  # Trả về người nhận (participant)
        return obj['sender']  # Trả về người gửi (participant)

    def to_representation(self, instance):
        # Trả về thông tin người tham gia (participant)
        representation = super().to_representation(instance)
        participant = self.get_participant(instance)  # Lấy thông tin người tham gia
        representation['participant'] = participant.username  # Trả về username của participant
        return representation