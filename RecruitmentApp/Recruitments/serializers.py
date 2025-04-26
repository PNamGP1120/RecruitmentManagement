import re

from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core import validators
from difflib import SequenceMatcher
from .models import Role, UserRole, NtvProfile, CV, NtdProfile, Application

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer cho đăng ký người dùng. KHÔNG gán role ngay khi tạo tài khoản.
    """
    username = serializers.CharField(
        max_length=150,
        validators=[validators.RegexValidator(r'^[a-zA-Z0-9._-]+$', message="Chỉ cho phép chữ cái, số, dấu chấm, gạch dưới và gạch ngang.")]
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

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Tên người dùng này đã tồn tại.")
        return value

    def validate(self, data):
        password = data.get('password')
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Mật khẩu không khớp.")

        # Kiểm tra độ dài mật khẩu thủ công
        if password and len(password) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")

        # Kiểm tra độ mạnh mật khẩu thủ công
        if password and not (re.search(r'[A-Z]', password) and
                             re.search(r'\d', password) and
                             re.search(r'[\W_]', password)):
            raise serializers.ValidationError(
                "Mật khẩu không đủ mạnh. Phải có ít nhất 8 ký tự, một chữ cái viết hoa, một số và một ký tự đặc biệt."
            )

        # Kiểm tra tương đồng mật khẩu thủ công
        user = User(username=data['username'], email=data['email'])
        if password and any(SequenceMatcher(None, password.lower(), getattr(user, attr, '').lower()).quick_ratio() >= 0.7
                           for attr in ['username', 'email'] if getattr(user, attr, '')):
            raise serializers.ValidationError("Mật khẩu quá giống với tên người dùng hoặc email.")

        return data

    def create(self, validated_data):
        """
        Tạo User. KHÔNG tạo UserRole hoặc gán activeRole ở đây.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Tài khoản bị vô hiệu hóa.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Tên đăng nhập hoặc mật khẩu không đúng.")
        else:
            raise serializers.ValidationError("Vui lòng nhập tên đăng nhập và mật khẩu.")
        return data


class NtdRequestSerializer(serializers.Serializer):
    """
    Serializer cho yêu cầu trở thành Nhà tuyển dụng.
    """
    message = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        user = self.context['request'].user
        ntd_role = Role.objects.get(roleName=Role.NTD)
        # Kiểm tra xem người dùng đã có vai trò NTD chưa hoặc đã gửi yêu cầu chưa
        if not UserRole.objects.filter(user=user, role=ntd_role).exists():
            UserRole.objects.create(user=user, role=ntd_role, isApproved=False)
            return {'message': 'Yêu cầu trở thành Nhà tuyển dụng đã được gửi thành công. Vui lòng chờ phê duyệt từ quản trị viên.'}
        else:
            raise serializers.ValidationError("Bạn đã là Nhà tuyển dụng hoặc đã gửi yêu cầu trước đó.")


class ApproveNtdRequestSerializer(serializers.Serializer):
    """
    Serializer cho phê duyệt yêu cầu trở thành Nhà tuyển dụng.
    """
    user_id = serializers.IntegerField(required=True)
    is_approved = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        instance.isApproved = validated_data.get('is_approved', instance.isApproved)
        instance.approvedAt = timezone.now() if instance.isApproved else None
        instance.approvedBy = self.context['request'].user
        instance.save()
        return instance


class CVSerializer(serializers.ModelSerializer):
    """
    Serializer cho CV.
    """
    ntv_profile = serializers.PrimaryKeyRelatedField(read_only=True)
    file_path = serializers.SerializerMethodField()
    file_data = serializers.FileField(write_only=True)  # Cho phép upload file khi tạo

    class Meta:
        model = CV
        fields = ['id', 'ntv_profile', 'fileName', 'file_path', 'file_data', 'versionName', 'isDefault', 'uploadDate']
        read_only_fields = ['id', 'uploadDate', 'ntv_profile', 'file_path']

    @staticmethod
    def get_file_path(obj):
        """
        Trả về URL của file từ trường filePath (CloudinaryField).
        """
        if obj.filePath and hasattr(obj.filePath, 'url'):
            return obj.filePath.url
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            ntv_profile = user.ntv_profile
        except NtvProfile.DoesNotExist:
            raise serializers.ValidationError("Người dùng này không có NtvProfile.")

        file_data = validated_data.pop('file_data')
        validated_data.pop('ntv_profile', None)
        cv = CV.objects.create(ntv_profile=ntv_profile, filePath=file_data, **validated_data)
        return cv


# class NtvProfileSerializer(serializers.ModelSerializer):
#     """
#     Serializer cho NtvProfile.  Gán role NTV khi tạo hoặc cập nhật hồ sơ.
#     """
#     user = serializers.PrimaryKeyRelatedField(read_only=True)
#
#     class Meta:
#         model = NtvProfile
#         fields = '__all__'
#         read_only_fields = ('user',)
#
#     def create(self, validated_data):
#         user = self.context['request'].user
#         ntv_profile = NtvProfile.objects.create(user=user, **validated_data)
#
#         # Kích hoạt vai trò NTV khi tạo hồ sơ
#         ntv_role = Role.objects.get(roleName=Role.NTV)
#         UserRole.objects.get_or_create(user=user, role=ntv_role, defaults={'isApproved': True, 'approvedAt': timezone.now()})
#         user.activeRole = ntv_role
#         user.save()
#
#         return ntv_profile
#
#     def update(self, instance, validated_data):
#         instance.summary = validated_data.get('summary', instance.summary)
#         instance.experience = validated_data.get('experience', instance.experience)
#         instance.education = validated_data.get('education', instance.education)
#         instance.skills = validated_data.get('skills', instance.skills)
#         instance.phoneNumber = validated_data.get('phoneNumber', instance.phoneNumber)
#         instance.dateOfBirth = validated_data.get('dateOfBirth', instance.dateOfBirth)
#         instance.gender = validated_data.get('gender', instance.gender)
#         instance.save()
#
#         # Kích hoạt vai trò NTV khi cập nhật hồ sơ
#         ntv_role = Role.objects.get(roleName=Role.NTV)
#         UserRole.objects.get_or_create(user=instance.user, role=ntv_role, defaults={'isApproved': True, 'approvedAt': timezone.now()})
#         instance.user.activeRole = ntv_role
#         instance.user.save()
#
#         return instance
#
#     @staticmethod
#     def activate_ntv_role(user):
#         """Hàm nội bộ để kích hoạt vai trò Người tìm việc cho người dùng."""
#         ntv_role = Role.objects.get(roleName='NTV')
#         UserRole.objects.get_or_create(
#             user=user,
#             role=ntv_role,
#             defaults={'isApproved': True, 'approvedAt': timezone.now()}
#         )
#         user.activeRole = ntv_role
#         user.save()

from rest_framework import serializers
from .models import NtvProfile, Role, UserRole
from django.utils import timezone

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
        ntv_profile = NtvProfile.objects.create(user=user, **validated_data)
        self.activate_ntv_role(user)
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
        self.activate_ntv_role(instance.user)
        return instance

    @staticmethod
    def activate_ntv_role(user):
        """Hàm nội bộ để kích hoạt vai trò Người tìm việc cho người dùng."""
        ntv_role = Role.objects.get(roleName='NTV')
        UserRole.objects.get_or_create(
            user=user,
            role=ntv_role,
            defaults={'isApproved': True, 'approvedAt': timezone.now()}
        )
        user.activeRole = ntv_role
        user.save()

class UserAndNtvProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer để cập nhật thông tin User và tạo NtvProfile (nếu chưa tồn tại).
    """
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    summary = serializers.CharField(required=False, allow_blank=True)
    experience = serializers.CharField(required=False, allow_blank=True)
    education = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)
    phoneNumber = serializers.CharField(max_length=15, required=False, allow_blank=True)
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=1, required=False, allow_blank=True)

    def update(self, instance, validated_data):
        # Cập nhật thông tin User
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()

        # Tạo hoặc cập nhật NtvProfile
        ntv_profile_data = {
            'summary': validated_data.get('summary'),
            'experience': validated_data.get('experience'),
            'education': validated_data.get('education'),
            'skills': validated_data.get('skills'),
            'phoneNumber': validated_data.get('phoneNumber'),
            'dateOfBirth': validated_data.get('dateOfBirth'),
            'gender': validated_data.get('gender'),
        }
        NtvProfile.objects.update_or_create(user=instance, defaults=ntv_profile_data)

        return instance

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer để cập nhật thông tin tài khoản người dùng.
    """
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'avatar')
        read_only_fields = ('username', 'date_joined', 'last_login', 'is_staff', 'is_superuser', 'is_active')

from rest_framework import serializers
from .models import NtdProfile, Role, UserRole

class NtdProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho model NtdProfile. Tự động gửi yêu cầu phê duyệt NTD khi tạo hoặc cập nhật.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = NtdProfile
        fields = '__all__'
        # read_only_fields = ('user',)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('user', None)  # Loại bỏ 'user' khỏi validated_data nếu nó tồn tại
        ntd_profile = NtdProfile.objects.create(user=user, **validated_data)
        self.request_ntd_approval(user)
        return ntd_profile

    def update(self, instance, validated_data):
        instance.companyName = validated_data.get('companyName', instance.companyName)
        instance.companyWebsite = validated_data.get('companyWebsite', instance.companyWebsite)
        instance.companyDescription = validated_data.get('companyDescription', instance.companyDescription)
        instance.industry = validated_data.get('industry', instance.industry)
        instance.address = validated_data.get('address', instance.address)
        instance.companyLogo = validated_data.get('companyLogo', instance.companyLogo)
        instance.save()
        self.request_ntd_approval(instance.user)
        return instance

    @staticmethod
    def request_ntd_approval(user):
        """Hàm nội bộ để gửi yêu cầu phê duyệt vai trò Nhà tuyển dụng cho người dùng."""
        ntd_role = Role.objects.get(roleName='NTD')
        UserRole.objects.get_or_create(
            user=user,
            role=ntd_role,
            defaults={'isApproved': False}
        )
        # Chúng ta không tự động set activeRole ở đây.
        # Quản trị viên sẽ phê duyệt và người dùng có thể chọn activeRole sau.

from rest_framework import serializers
from .models import JobPosting, NtdProfile

class JobPostingSerializer(serializers.ModelSerializer):
    """
    Serializer cho model JobPosting.
    """
    ntd_profile = serializers.PrimaryKeyRelatedField(queryset=NtdProfile.objects, write_only=True)
    # ntd_profile_detail = NtdProfileSerializer(read_only=True, source='ntd_profile') # Để hiển thị thông tin NTD khi đọc

    class Meta:
        model = JobPosting
        fields = '__all__'
        read_only_fields = ('id', 'createdAt', 'isActive')

class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Application (Hồ sơ ứng tuyển).
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True) # Người dùng là read-only (tự động lấy từ request)
    job_posting = serializers.PrimaryKeyRelatedField(queryset=JobPosting.objects)
    cv = serializers.PrimaryKeyRelatedField(queryset=CV.objects, allow_null=True, required=False)
    coverLetter = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Application
        fields = ['id', 'user', 'job_posting', 'cv', 'coverLetter', 'submittedAt', 'status']
        read_only_fields = ['id', 'submittedAt', 'status', 'user'] # submittedAt và status được tự động quản lý

