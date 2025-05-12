from django.contrib import admin
from .models import Role, UserRole, User, NtdProfile, NtvProfile, CV, JobPosting, Application, Message, Interview, \
    Notification, Skill


class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'id')
    search_fields = ['role_name']
    list_filter = ['role_name']


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'active_role', 'is_active', 'date_joined')
    search_fields = ['username', 'email']
    list_filter = ['active_role', 'is_active', 'date_joined']
    list_editable = ['active_role']


class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_approved', 'approved_at')
    search_fields = ['user__username', 'role__role_name']
    list_filter = ['role', 'is_approved']
    list_editable = ['is_approved']


class NtdProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'industry', 'company_website', 'address')
    search_fields = ['company_name', 'user__username']
    list_filter = ['industry', 'company_name']
    readonly_fields = ['user']


class NtvProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'phone_number', 'date_of_birth', 'summary')
    search_fields = ['user__username', 'gender', 'phone_number']
    list_filter = ['gender', 'date_of_birth']
    readonly_fields = ['user']


class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['name']
    list_filter = ['name']
    list_editable = ['name']
    list_display_links = ('id',)


class CVAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'ntv_profile', 'version_name', 'is_default', 'is_deleted')
    search_fields = ['file_name', 'ntv_profile__user__username']
    list_filter = ['is_default', 'is_deleted']
    list_editable = ['is_default']


class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'ntd_profile', 'location', 'salary_min', 'salary_max', 'job_type', 'is_active')
    search_fields = ['title', 'ntd_profile__company_name', 'location']
    list_filter = ['job_type', 'is_active', 'ntd_profile__company_name']
    list_editable = ['is_active']


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_posting', 'status', 'cv', 'cover_letter')
    search_fields = ['user__username', 'job_posting__title']
    list_filter = ['status', 'job_posting__title']
    list_editable = ['status']


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'content', 'is_read', 'read_at')
    search_fields = ['sender__username', 'recipient__username', 'content']
    list_filter = ['is_read', 'read_at']


class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_time', 'status', 'result')
    search_fields = ['application__user__username', 'status']
    list_filter = ['status', 'result']


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'is_read', 'message', 'related_url')
    search_fields = ['recipient__username', 'message', 'type']
    list_filter = ['type', 'is_read']


# Register models with their respective admin classes
admin.site.register(Role, RoleAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserRole, UserRoleAdmin)
admin.site.register(NtdProfile, NtdProfileAdmin)
admin.site.register(NtvProfile, NtvProfileAdmin)
admin.site.register(CV, CVAdmin)

admin.site.register(JobPosting, JobPostingAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Interview, InterviewAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Skill, SkillAdmin)
