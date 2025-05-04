import re

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core import validators
from difflib import SequenceMatcher
from .models import Message
from . import firebase_config

from .models import Role, UserRole, NtvProfile, NtdProfile, JobPosting, CV, Application, Interview, Notification

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer cho đăng ký người dùng. KHÔNG gán role ngay khi tạo tài khoản.
    """
    username = serializers.CharField(
        max_length=150,
        validators=[validators.RegexValidator(r'^[a-zA-Z0-9._-]+$',
                                              message="Chỉ cho phép chữ cái, số, dấu chấm, gạch dưới và gạch ngang.")]
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    @staticmethod
    def validate_username(value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Tên người dùng này đã tồn tại.")
        return value

    def validate(self, data):
        password = data.get('password')
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Mật khẩu không khớp.")

        if password and len(password) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")

        if password and not (re.search(r'[A-Z]', password) and
                             re.search(r'\d', password) and
                             re.search(r'[\W_]', password)):
            raise serializers.ValidationError(
                "Mật khẩu không đủ mạnh. Phải có ít nhất 8 ký tự, một chữ cái viết hoa, một số và một ký tự đặc biệt."
            )

        user = User(username=data['username'], email=data['email'])
        if password and any(
                SequenceMatcher(None, password.lower(), getattr(user, attr, '').lower()).quick_ratio() >= 0.7
                for attr in ['username', 'email'] if getattr(user, attr, '')):
            raise serializers.ValidationError("Mật khẩu quá giống với tên người dùng hoặc email.")

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class NtdRequestSerializer(serializers.Serializer):
    """
    Serializer cho yêu cầu trở thành Nhà tuyển dụng.
    """
    message = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = self.context['request'].user
        ntd_role = Role.objects.get(roleName=Role.NTD)
        if not UserRole.objects.filter(user=user, role=ntd_role).exists():
            UserRole.objects.create(user=user, role=ntd_role, isApproved=False)
            return {'message': 'Yêu cầu trở thành Nhà tuyển dụng đã được gửi thành công. Vui lòng chờ phê duyệt từ quản trị viên.'}
        else:
            raise serializers.ValidationError("Bạn đã là Nhà tuyển dụng hoặc đã gửi yêu cầu trước đó.")

class NtdProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    # Trả về url đầy đủ của hình ảnh
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['companyLogo'] = instance.companyLogo.url if instance.companyLogo.url else ''
        return data

    class Meta:
        model = NtdProfile
        fields = '__all__'
        read_only_fields = ('user',)

    def create(self, validated_data):
        user = self.context['request'].user
        company_name = validated_data.get('companyName')
        company_website = validated_data.get('companyWebsite')
        company_description = validated_data.get('companyDescription')
        industry = validated_data.get('industry')
        address = validated_data.get('address')
        company_logo = validated_data.get('companyLogo')

        ntd_profile = NtdProfile.objects.create(
            user=user,
            companyName=company_name,
            companyWebsite=company_website,
            companyDescription=company_description,
            industry=industry,
            address=address,
            companyLogo=company_logo
        )

        # Tạo UserRole với vai trò NTD và isApproved=False
        ntd_role = Role.objects.get(roleName=Role.NTD)
        UserRole.objects.create(user=user, role=ntd_role, isApproved=False)

        return ntd_profile

class ApproveNtdRequestSerializer(serializers.Serializer):
    """
    Serializer cho phê duyệt yêu cầu trở thành Nhà tuyển dụng.
    """

    user_id = serializers.IntegerField(required=True)
    isApproved = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        print(
            f"Before update - validated_data['is_approved']: {validated_data.get('is_approved')}, instance.isApproved: {instance.isApproved}")
        instance.isApproved = validated_data.get('is_approved', instance.isApproved)
        print(f"After update - instance.isApproved: {instance.isApproved}")
        instance.approvedAt = timezone.now() if instance.isApproved else None
        instance.approvedBy = self.context['request'].user
        instance.save()
        print(f"After save - instance.isApproved: {instance.isApproved}")
        print(instance)
        return instance

class NtvProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho NtvProfile. Kích hoạt role NTV khi tạo hoặc cập nhật hồ sơ.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = NtvProfile
        fields = '__all__'
        read_only_fields = ('user',)

    def create(self, validated_data):
        user = self.context['request'].user
        summary = validated_data.get('summary')
        experience = validated_data.get('experience')
        education = validated_data.get('education')
        skills = validated_data.get('skills')
        phone_number = validated_data.get('phoneNumber')
        date_of_birth = validated_data.get('dateOfBirth')
        gender = validated_data.get('gender')

        print("Summary:", summary)
        print("Experience:", experience)
        # ... và các trường khác

        ntv_profile = NtvProfile.objects.create(
            user=user,
            summary=summary,
            experience=experience,
            education=education,
            skills=skills,
            phoneNumber=phone_number,
            dateOfBirth=date_of_birth,
            gender=gender
        )
        self._activate_ntv_role(user)
        return ntv_profile

    def update(self, instance, validated_data):
        instance.summary = validated_data.get('summary', instance.summary)
        instance.experience = validated_data.get('experience', instance.experience)
        instance.education = validated_data.get('education', instance.education)
        instance.skills = validated_data.get('skills', instance.skills)
        instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
        instance.dateOfBirth = validated_data.get('dateOfBirth', instance.dateOfBirth)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.save()
        self._activate_ntv_role(instance.user)
        return instance

    @staticmethod
    def _activate_ntv_role(user):
        """Hàm nội bộ để kích hoạt vai trò Người tìm việc cho người dùng."""
        ntv_role = Role.objects.get(roleName='NTV')
        UserRole.objects.get_or_create(
            user=user,
            role=ntv_role,
            defaults={'isApproved': True, 'approvedAt': timezone.now()}
        )
        user.activeRole = ntv_role
        user.save()

class ChangeActiveRoleSerializer(serializers.Serializer):
    activeRole = serializers.CharField(max_length=20)

    def update(self, instance, validated_data):
        instance.activeRole = validated_data.get('activeRole', instance.activeRole)
        # Cần thêm logic để kiểm tra xem user có role được chọn hay không
        instance.save()
        return instance

class JobPostingSerializer(serializers.ModelSerializer):
    """
    Serializer cho model JobPosting.
    """
    ntd_profile = serializers.PrimaryKeyRelatedField(queryset=NtdProfile.objects, write_only=True, required=False)
    # Để hiển thị thông tin NTD khi đọc (tùy chọn)
    ntd_profile_detail = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = '__all__'
        read_only_fields = ('id', 'createdAt', 'isActive')

    @staticmethod
    def get_ntd_profile_detail(obj):
        return NtdProfileSerializer(obj.ntd_profile).data if obj.ntd_profile else None

    def create(self, validated_data):
        ntd_profile = self.context['request'].user.ntdprofile
        return JobPosting.objects.create(**validated_data, isActive=False)

class ApproveJobPostingSerializer(serializers.ModelSerializer):
    """
    Serializer cho phép Admin phê duyệt (cập nhật isActive) tin tuyển dụng.
    """
    class Meta:
        model = JobPosting
        fields = ['id', 'isActive']
        read_only_fields = ['id']

class CVSeralizer(serializers.ModelSerializer):
    """
    Serializer cho model CV.
    """
    ntv_profile = serializers.PrimaryKeyRelatedField(queryset=NtvProfile.objects, write_only=True, required=False)

    class Meta:
        model = CV
        fields = '__all__'
        read_only_fields = ('id', 'uploadDate', 'ntv_profile')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['filePath'] = instance.filePath.url if instance.filePath else None
        return rep

class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Application.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    job_posting = serializers.PrimaryKeyRelatedField(queryset=JobPosting.objects)
    cv = serializers.PrimaryKeyRelatedField(queryset=CV.objects, allow_null=True, required=False)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('id', 'submittedAt', 'user')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class InterviewSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Interview.
    """
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects)

    class Meta:
        model = Interview
        fields = '__all__'
        read_only_fields = ('id',)

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Notification.
    """
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'createdAt', 'isRead', 'recipient')

    def create(self, validated_data):
        validated_data['recipient'] = self.context['request'].user
        return super().create(validated_data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'recipient_id', 'recipient', 'content', 'timestamp')
        read_only_fields = ('id', 'sender', 'recipient', 'timestamp')

    def create(self, validated_data):
        sender = self.context['request'].user
        recipient_id = validated_data.pop('recipient_id')
        validated_data.pop('sender', None)
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient_id": "Người dùng không tồn tại."})
        message = Message.objects.create(sender=sender, recipient=recipient, **validated_data)
        self.send_to_firebase(message)  # Gọi hàm gửi lên Firebase sau khi tạo message
        return message

    @staticmethod
    def send_to_firebase(message):
        """Gửi thông tin tin nhắn lên Firebase Realtime Database."""
        try:
            ref = firebase_config.db.reference(f'messages/{message.recipient.id}/{message.sender.id}')
            ref.push({
                'sender_id': message.sender.id,
                'recipient_id': message.recipient.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            })
            ref_reverse = firebase_config.db.reference(f'messages/{message.sender.id}/{message.recipient.id}')
            ref_reverse.push({
                'sender_id': message.sender.id,
                'recipient_id': message.recipient.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            })
            print(f"Đã gửi tin nhắn ID {message.id} lên Firebase.")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn ID {message.id} lên Firebase: {e}")

