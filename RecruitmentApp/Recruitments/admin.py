from django.contrib import admin
from .models import Role, UserRole, MyUser, JobSeekerProfile, RecruiterProfile, CV, JobPosting, Application, Message, Interview, \
    Notification, Skill


admin.site.register(Role)
admin.site.register(UserRole)
admin.site.register(MyUser)
admin.site.register(JobSeekerProfile)
admin.site.register(RecruiterProfile)
admin.site.register(CV)
admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Message)
admin.site.register(Interview)
admin.site.register(Notification)
admin.site.register(Skill)

