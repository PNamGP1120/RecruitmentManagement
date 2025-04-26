from django.contrib import admin
from .models import Role, UserRole, User, NtdProfile, NtvProfile, CV, JobPosting, Application, Conversation, ChatMessage, Interview, Notification

admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(User)
admin.site.register(NtdProfile)
admin.site.register(NtvProfile)
admin.site.register(CV)
admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Conversation)
admin.site.register(ChatMessage)
admin.site.register(Interview)
admin.site.register(Notification)