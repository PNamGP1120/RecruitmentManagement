# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Nên dùng settings.AUTH_USER_MODEL

# Import CloudinaryField
from cloudinary.models import CloudinaryField

# 1. Role Model
class Role(models.Model):
    """
    Định nghĩa các vai trò trong hệ thống (NTV, NTD, Admin).
    """
    NTV = 'NTV'
    NTD = 'NTD'
    ADMIN = 'Admin'
    ROLE_CHOICES = [
        (NTV, 'Người tìm việc'),
        (NTD, 'Nhà tuyển dụng'),
        (ADMIN, 'Quản trị viên'),
    ]
    # roleId sẽ tự động được tạo bởi Django (là trường id)
    roleName = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True, verbose_name="Tên vai trò")

    def __str__(self):
        return self.get_roleName_display() # Hiển thị tên đầy đủ

    class Meta:
        verbose_name = "Vai trò"
        verbose_name_plural = "Các vai trò"

# 2. User Model (Kế thừa AbstractUser)
class User(AbstractUser):
    """
    Model người dùng cốt lõi, kế thừa từ AbstractUser của Django.
    Thêm các trường để quản lý vai trò hoạt động và liên kết hồ sơ.
    """
    # Bỏ các trường không dùng từ AbstractUser nếu cần (first_name, last_name?)
    # email đã có và là unique=True theo mặc định nếu USERNAME_FIELD='email'
    # password đã có
    # isActive đã có (is_active)
    # createdAt đã có (date_joined)

    # Sử dụng ForeignKey thay vì lưu trực tiếp đối tượng Role
    # Cho phép null để user mới đăng ký chưa chọn vai trò hoạt động ngay
    activeRole = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL, # Hoặc PROTECT nếu vai trò là bắt buộc
        null=True,
        blank=True,
        verbose_name="Vai trò đang hoạt động"
    )
    # Sửa CloudinaryField: Bỏ đối số vị trí 'image'
    avatar = CloudinaryField(null=True, blank=True, folder='avatars', verbose_name="Ảnh đại diện")

    # Trường ManyToMany đến Role thông qua UserRole sẽ được định nghĩa trong UserRole
    # hoặc có thể truy cập qua related_name

    # Các phương thức như login, register, etc. sẽ nằm trong views/serializers
    # Các phương thức getProfileNTV, getProfileNTD có thể là property hoặc method

    @property
    def ntv_profile(self):
        # Trả về NtvProfile nếu có, nếu không trả về None
        return getattr(self, 'ntvprofile', None) # 'ntvprofile' là related_name mặc định

    @property
    def ntd_profile(self):
         # Trả về NtdProfile nếu có, nếu không trả về None
        return getattr(self, 'ntdprofile', None) # 'ntdprofile' là related_name mặc định

    # Cung cấp URL avatar (nếu có)
    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        # Cung cấp URL mặc định nếu không có avatar hoặc không dùng Cloudinary
        # Bạn có thể cần điều chỉnh URL mặc định này
        # Đảm bảo bạn có file ảnh này trong thư mục static/images
        return settings.STATIC_URL + 'images/default_avatar.png'

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"


# 3. UserRole Model (Bảng trung gian User-Role)
class UserRole(models.Model):
    """
    Liên kết giữa User và Role, lưu trạng thái phê duyệt cho vai trò NTD.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_roles', verbose_name="Người dùng")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users', verbose_name="Vai trò")
    isApproved = models.BooleanField(default=False, verbose_name="Đã phê duyệt (cho NTD)")
    approvedAt = models.DateTimeField(null=True, blank=True, verbose_name="Ngày phê duyệt")
    approvedBy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_roles', # Người Admin đã phê duyệt
        verbose_name="Người phê duyệt"
    )

    def getRoleName(self):
        return self.role.roleName

    def __str__(self):
        approval_status = " (Đã phê duyệt)" if self.isApproved else " (Chưa phê duyệt)" if self.role.roleName == Role.NTD else ""
        return f"{self.user.username} - {self.role.get_roleName_display()}{approval_status}"

    class Meta:
        unique_together = ('user', 'role') # Mỗi user chỉ có 1 bản ghi cho mỗi role
        verbose_name = "Vai trò người dùng"
        verbose_name_plural = "Các vai trò người dùng"

# 4. NtvProfile Model (Hồ sơ Người tìm việc)
class NtvProfile(models.Model):
    """
    Lưu trữ thông tin chi tiết cho vai trò Người tìm việc (NTV).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='ntvprofile', verbose_name="Người dùng")
    # profileId chính là user_id do dùng OneToOneField với primary_key=True
    summary = models.TextField(blank=True, null=True, verbose_name="Giới thiệu bản thân")
    experience = models.TextField(blank=True, null=True, verbose_name="Kinh nghiệm làm việc")
    education = models.TextField(blank=True, null=True, verbose_name="Học vấn")
    skills = models.TextField(blank=True, null=True, verbose_name="Kỹ năng (phân cách bởi dấu phẩy)") # Hoặc dùng ManyToMany nếu muốn chuẩn hóa skills
    phoneNumber = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    dateOfBirth = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    GENDER_CHOICES = [('M', 'Nam'), ('F', 'Nữ'), ('O', 'Khác')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Giới tính")
    # Các phương thức manageProfile, addCV, removeCV sẽ nằm trong views/serializers

    def __str__(self):
        return f"Hồ sơ NTV của {self.user.username}"

    class Meta:
        verbose_name = "Hồ sơ Người tìm việc"
        verbose_name_plural = "Các hồ sơ Người tìm việc"

# 5. NtdProfile Model (Hồ sơ Nhà tuyển dụng)
class NtdProfile(models.Model):
    """
    Lưu trữ thông tin chi tiết cho vai trò Nhà tuyển dụng (NTD).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='ntdprofile', verbose_name="Người dùng")
    # profileId chính là user_id
    companyName = models.CharField(max_length=255, verbose_name="Tên công ty")
    companyWebsite = models.URLField(blank=True, null=True, verbose_name="Website công ty")
    companyDescription = models.TextField(blank=True, null=True, verbose_name="Mô tả công ty")
    industry = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ngành nghề")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Địa chỉ công ty")
    # Sửa CloudinaryField: Bỏ đối số vị trí 'image'
    companyLogo = CloudinaryField(blank=True, null=True, folder='company_logos', verbose_name="Logo công ty")
    # Các phương thức manageProfile, postJob sẽ nằm trong views/serializers

    def __str__(self):
        return f"Hồ sơ NTD của {self.companyName} ({self.user.username})"

    class Meta:
        verbose_name = "Hồ sơ Nhà tuyển dụng"
        verbose_name_plural = "Các hồ sơ Nhà tuyển dụng"


# 6. CV Model
class CV(models.Model):
    """
    Đại diện cho một hồ sơ CV của Người tìm việc.
    """
    # cvId tự động tạo
    ntv_profile = models.ForeignKey(NtvProfile, on_delete=models.CASCADE, related_name='cvs', verbose_name="Hồ sơ NTV")
    fileName = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tên file gốc")
    # Sửa CloudinaryField: Bỏ đối số vị trí 'raw', thêm resource_type='raw'
    filePath = CloudinaryField(resource_type='raw', folder='cvs', verbose_name="File CV")
    versionName = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tên phiên bản (e.g., CV Tiếng Anh)")
    uploadDate = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tải lên")
    isDefault = models.BooleanField(default=False, verbose_name="Là CV mặc định")
    # Các phương thức upload, preview, delete, extractInfoOCR sẽ nằm trong views/serializers/services

    def __str__(self):
        return f"CV '{self.versionName or self.fileName or self.id}' của {self.ntv_profile.user.username}"

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "Các CV"


# 7. JobPosting Model (Tin tuyển dụng)
class JobPosting(models.Model):
    """
    Đại diện cho một tin tuyển dụng được đăng bởi Nhà tuyển dụng.
    """
    # jobId tự động tạo
    ntd_profile = models.ForeignKey(NtdProfile, on_delete=models.CASCADE, related_name='job_postings', verbose_name="Hồ sơ NTD")
    title = models.CharField(max_length=255, verbose_name="Tiêu đề công việc")
    description = models.TextField(verbose_name="Mô tả công việc")
    location = models.CharField(max_length=255, verbose_name="Địa điểm làm việc")
    salaryMin = models.FloatField(null=True, blank=True, verbose_name="Lương tối thiểu")
    salaryMax = models.FloatField(null=True, blank=True, verbose_name="Lương tối đa")
    experienceRequired = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kinh nghiệm yêu cầu")
    JOB_TYPE_CHOICES = [
        ('Full-time', 'Toàn thời gian'),
        ('Part-time', 'Bán thời gian'),
        ('Freelance', 'Freelance'),
        ('Internship', 'Thực tập'),
    ]
    jobType = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, verbose_name="Loại hình công việc")
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng")
    expiresAt = models.DateTimeField(null=True, blank=True, verbose_name="Ngày hết hạn")
    isActive = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    # Các phương thức editJob, closeJob, getApplications sẽ nằm trong views/serializers

    def __str__(self):
        return f"{self.title} tại {self.ntd_profile.companyName}"

    class Meta:
        verbose_name = "Tin tuyển dụng"
        verbose_name_plural = "Các tin tuyển dụng"
        ordering = ['-createdAt'] # Sắp xếp theo ngày tạo mới nhất


# 8. Application Model (Hồ sơ ứng tuyển)
class Application(models.Model):
    """
    Đại diện cho việc một NTV ứng tuyển vào một JobPosting bằng một CV.
    """
    # applicationId tự động tạo
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications', verbose_name="Người ứng tuyển (NTV)")
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications', verbose_name="Tin tuyển dụng")
    cv = models.ForeignKey(CV, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications', verbose_name="CV đã sử dụng") # Cho phép null nếu CV bị xóa
    submittedAt = models.DateTimeField(auto_now_add=True, verbose_name="Ngày ứng tuyển")
    STATUS_CHOICES = [
        ('Applied', 'Đã ứng tuyển'),
        ('Viewed', 'NTD đã xem'),
        ('Interviewing', 'Đang phỏng vấn'),
        ('Offered', 'Đã mời nhận việc'),
        ('Rejected', 'Đã từ chối'),
        ('Withdrawn', 'Ứng viên đã rút'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied', verbose_name="Trạng thái")
    coverLetter = models.TextField(blank=True, null=True, verbose_name="Thư xin việc")
    # Các phương thức trackStatus, updateStatus, withdraw sẽ nằm trong views/serializers

    def __str__(self):
        return f"{self.user.username} ứng tuyển vào {self.job_posting.title}"

    class Meta:
        unique_together = ('user', 'job_posting') # Mỗi user chỉ ứng tuyển 1 lần vào 1 job
        verbose_name = "Hồ sơ ứng tuyển"
        verbose_name_plural = "Các hồ sơ ứng tuyển"
        ordering = ['-submittedAt']


# 9. Conversation Model (Cuộc hội thoại)
class Conversation(models.Model):
    """
    Nhóm các tin nhắn giữa hai người dùng (thường là NTV và NTD).
    """
    # conversationId tự động tạo
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations', verbose_name="Người tham gia")
    lastMessageAt = models.DateTimeField(auto_now=True, verbose_name="Thời gian tin nhắn cuối") # Cập nhật khi có tin nhắn mới

    def __str__(self):
        usernames = " và ".join([user.username for user in self.participants.all()])
        return f"Hội thoại giữa {usernames}"

    class Meta:
        verbose_name = "Cuộc hội thoại"
        verbose_name_plural = "Các cuộc hội thoại"
        ordering = ['-lastMessageAt']

# 10. ChatMessage Model (Tin nhắn)
class ChatMessage(models.Model):
    """
    Đại diện cho một tin nhắn trong một cuộc hội thoại.
    """
    # messageId tự động tạo
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="Cuộc hội thoại")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Người gửi")
    content = models.TextField(verbose_name="Nội dung")
    sentAt = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian gửi")
    isRead = models.BooleanField(default=False, verbose_name="Đã đọc")
    # Phương thức markAsRead sẽ nằm trong views/logic xử lý

    def __str__(self):
        return f"Tin nhắn từ {self.sender.username} lúc {self.sentAt.strftime('%H:%M %d/%m')}"

    class Meta:
        verbose_name = "Tin nhắn"
        verbose_name_plural = "Các tin nhắn"
        ordering = ['sentAt'] # Sắp xếp theo thời gian gửi


# 11. Interview Model (Buổi phỏng vấn)
class Interview(models.Model):
    """
    Đại diện cho một buổi phỏng vấn được lên lịch.
    """
    # interviewId tự động tạo
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews', verbose_name="Hồ sơ ứng tuyển")
    # Người lên lịch (NTD) và người tham gia (NTV) có thể lấy từ application.job_posting.ntd_profile.user và application.user
    scheduledTime = models.DateTimeField(verbose_name="Thời gian dự kiến")
    platformLink = models.URLField(blank=True, null=True, verbose_name="Link phòng họp video")
    STATUS_CHOICES = [
        ('Scheduled', 'Đã lên lịch'),
        ('Completed', 'Đã hoàn thành'),
        ('Cancelled', 'Đã hủy'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled', verbose_name="Trạng thái")
    notesNtd = models.TextField(blank=True, null=True, verbose_name="Ghi chú của NTD")
    notesNtv = models.TextField(blank=True, null=True, verbose_name="Ghi chú của NTV") # Phản hồi sau PV
    RESULT_CHOICES = [
        ('Passed', 'Đạt'),
        ('Failed', 'Không đạt'),
        ('Pending', 'Chờ kết quả'),
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='Pending', blank=True, null=True, verbose_name="Kết quả")
    # Các phương thức schedule, reschedule, cancel, join, record, updateResult sẽ nằm trong views/serializers

    def __str__(self):
        return f"Phỏng vấn cho {self.application}"

    class Meta:
        verbose_name = "Buổi phỏng vấn"
        verbose_name_plural = "Các buổi phỏng vấn"
        ordering = ['scheduledTime']


# 12. Notification Model (Thông báo)
class Notification(models.Model):
    """
    Đại diện cho một thông báo gửi đến người dùng.
    """
    # notificationId tự động tạo
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name="Người nhận")
    message = models.TextField(verbose_name="Nội dung thông báo")
    TYPE_CHOICES = [
        ('NewJob', 'Việc làm mới phù hợp'),
        ('StatusUpdate', 'Cập nhật trạng thái ứng tuyển'),
        ('InterviewReminder', 'Nhắc lịch phỏng vấn'),
        ('ChatMessage', 'Tin nhắn mới'),
        ('System', 'Thông báo hệ thống'),
        # Thêm các loại khác nếu cần
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Loại thông báo")
    relatedUrl = models.URLField(blank=True, null=True, verbose_name="URL liên quan") # Link tới job, application, chat...
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    isRead = models.BooleanField(default=False, verbose_name="Đã đọc")
    # Phương thức markAsRead sẽ nằm trong views/logic xử lý

    def __str__(self):
        return f"Thông báo cho {self.recipient.username}: {self.get_type_display()}"

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Các thông báo"
        ordering = ['-createdAt']

