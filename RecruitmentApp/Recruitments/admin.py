from django.contrib import admin
from .models import Role, UserRole, User, NtdProfile, NtvProfile, CV, JobPosting, Application, Message, Interview, Notification

admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(User)
admin.site.register(NtdProfile)
admin.site.register(NtvProfile)
admin.site.register(CV)
admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Message)
admin.site.register(Interview)
admin.site.register(Notification)