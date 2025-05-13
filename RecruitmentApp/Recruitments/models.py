from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid
from cloudinary.models import CloudinaryField


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(models.Model):
    JobSeeker = 'JobSeeker'
    Recruiter = 'Recruiter'
    Admin = 'Admin'
    ROLE_CHOICES = [
        (JobSeeker, 'Người tìm việc'),
        (Recruiter, 'Nhà tuyển dụng'),
        (Admin, 'Quản trị viên'),
    ]
    role_name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_role_name_display()

    class Meta:
        verbose_name = "Vai trò"
        verbose_name_plural = "Các vai trò"
        ordering = ['role_name']


class MyUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = CloudinaryField(null=True, blank=True, folder='avatars')
    active_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username if self.username else "User has no username"

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else settings.STATIC_URL + 'images/default_avatar.png'

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"
        ordering = ['username']


class UserRole(models.Model):
    my_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_roles')

    class Meta:
        unique_together = ('my_user', 'role')
        verbose_name = "Vai trò người dùng"
        verbose_name_plural = "Các vai trò người dùng"
        ordering = ['my_user__username']

    def __str__(self):
        status = '(Đã phê duyệt)' if self.is_approved else ''
        return f"{self.my_user.username} - {self.role.get_role_name_display()} {status}"


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kỹ năng"
        verbose_name_plural = "Các kỹ năng"
        ordering = ['name']


class JobSeekerProfile(BaseModel):
    my_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
                                related_name='ntv_profile')
    summary = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = [('M', 'Nam'), ('F', 'Nữ'), ('O', 'Khác')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"Hồ sơ NTV của {self.my_user.username}"

    class Meta:
        verbose_name = "Hồ sơ người tìm việc"
        verbose_name_plural = "Các hồ sơ người tìm việc"
        ordering = ['my_user__username']


class RecruiterProfile(BaseModel):
    my_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
                                related_name='ntd_profile')
    company_name = models.CharField(max_length=255)
    company_website = models.URLField(blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    company_logo = CloudinaryField(blank=True, null=True, folder='company_logos')

    def __str__(self):
        return f"{self.company_name} ({self.my_user.username})"

    class Meta:
        verbose_name = "Hồ sơ Nhà tuyển dụng"
        verbose_name_plural = "Hồ sơ Nhà tuyển dụng"
        ordering = ['company_name']


class CV(BaseModel):
    job_seeker_profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='cvs')
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_path = CloudinaryField(resource_type='raw', folder='cvs')
    version_name = models.CharField(max_length=100, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"CV {self.version_name or self.file_name or self.id}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "Các CV"
        ordering = ['file_name']


class JobPosting(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter_profile = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary_min = models.FloatField(null=True, blank=True)
    salary_max = models.FloatField(null=True, blank=True)
    experience_required = models.CharField(max_length=100, blank=True, null=True)

    JOB_TYPE_CHOICES = [
        ('Full-time', 'Toàn thời gian'),
        ('Part-time', 'Bán thời gian'),
        ('Freelance', 'Freelance'),
        ('Internship', 'Thực tập')
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)  # Ngày hết hạn

    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('pending_approval', 'Chờ phê duyệt'),
        ('approved', 'Đã phê duyệt'),
        ('closed', 'Đã đóng'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def close_job(self):
        """
        Đóng tin tuyển dụng, thay đổi trạng thái thành 'closed'.
        """
        self.status = 'closed'
        self.is_active = False
        self.save()

    def approve_job(self):
        """Phê duyệt tin tuyển dụng, thay đổi trạng thái thành 'approved'"""
        self.status = 'approved'
        self.save()

    def reject_job(self):
        """Từ chối tin tuyển dụng, thay đổi trạng thái về 'draft'"""
        self.status = 'draft'
        self.save()

    def save(self, *args, **kwargs):
        """
        Tạo slug tự động khi title thay đổi và kiểm tra nếu trạng thái hết hạn.
        """
        # Tạo slug mới nếu chưa có hoặc nếu title đã thay đổi
        if not self.slug or self.title != self.slug:
            base_slug = slugify(self.title)
            base_slug = base_slug.replace('_', '-')  # Loại bỏ dấu gạch dưới nếu có
            slug = base_slug
            count = 1
            while JobPosting.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        # Kiểm tra nếu bài đăng đã hết hạn và tự động đóng bài đăng nếu hết hạn
        if self.expiration_date and self.expiration_date < timezone.now():
            self.close_job()

        # Lưu các thay đổi
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} tại {self.recruiter_profile.company_name}"

    class Meta:
        verbose_name = "Bài đăng tuyển dụng"
        verbose_name_plural = "Các bài đăng tuyển dụng"
        ordering = ['created_at']


class Application(BaseModel):
    my_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    cv = models.ForeignKey(CV, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    STATUS_CHOICES = [
        ('Applied', 'Đã ứng tuyển'),
        ('Viewed', 'NTD đã xem'),
        ('Interviewing', 'Đang phỏng vấn'),
        ('Offered', 'Đã mời nhận việc'),
        ('Rejected', 'Đã từ chối'),
        ('Withdrawn', 'Ứng viên đã rút')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    cover_letter = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('my_user', 'job_posting')
        verbose_name = "Đơn ứng tuyển"
        verbose_name_plural = "Các đơn ứng tuyển "
        ordering = ['my_user__username']

    def __str__(self):
        return f"{self.my_user.username} ứng tuyển vào {self.job_posting.title}"


class Message(BaseModel):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.content[:20]}..."

    class Meta:
        verbose_name = "Tin nhắn"
        verbose_name_plural = "Các tin nhắn"
        ordering = ['created_at']

    def mark_as_read(self):
        """
        Đánh dấu tin nhắn là đã đọc và cập nhật thời gian đọc.
        """
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        """
        Trước khi lưu tin nhắn, kiểm tra và đảm bảo rằng recipient không bị null.
        """
        if not self.recipient:
            raise ValueError("Recipient must be set.")
        super().save(*args, **kwargs)

class Interview(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduled_time = models.DateTimeField()
    platform_link = models.URLField(blank=True, null=True)
    STATUS_CHOICES = [
        ('Scheduled', 'Đã lên lịch'),
        ('Completed', 'Đã hoàn thành'),
        ('Cancelled', 'Đã hủy')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    notes_recruiter = models.TextField(blank=True, null=True)
    notes_job_seeker = models.TextField(blank=True, null=True)
    RESULT_CHOICES = [
        ('Passed', 'Đạt'),
        ('Failed', 'Không đạt'),
        ('Pending', 'Chờ kết quả')
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='Pending', blank=True, null=True)

    def __str__(self):
        return f"Phỏng vấn {self.application}"

    class Meta:
        verbose_name = "Cuộc phỏng vấn"
        verbose_name_plural = "Các cuộc phỏng vấn"
        unique_together = ('application',)


class Notification(BaseModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="sent_notifications")
    message = models.TextField()
    TYPE_CHOICES = [
        ('NewJob', 'Việc làm mới phù hợp'),
        ('StatusUpdate', 'Cập nhật trạng thái ứng tuyển'),
        ('InterviewReminder', 'Nhắc lịch phỏng vấn'),
        ('ChatMessage', 'Tin nhắn mới'),
        ('System', 'Thông báo hệ thống')
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    related_url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Thông báo cho {self.recipient.username}: {self.get_type_display()}"

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Các thông báo"


