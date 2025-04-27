from rest_framework import routers
from django.urls import path, include
from django.contrib import admin
from . import views
from .views import (
    RegistrationViewSet,
    BecomeNtdViewSet,
    ApproveNtdRequestViewSet,
    NtvProfileViewSet,
    ChangeActiveRoleViewSet,
    JobPostingViewSet,
    CVViewSet,
    ApplicationViewSet,
    InterviewViewSet,
    NotificationViewSet, NtdProfileViewSet, MessageViewSet
)

router = routers.DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='register')
router.register(r'ntd-request', BecomeNtdViewSet, basename='ntd-request')
router.register(r'approve-ntd-request', ApproveNtdRequestViewSet, basename='approve-ntd-request')
router.register(r'ntv-profile', NtvProfileViewSet, basename='ntv-profile')
router.register(r'change-active-role', ChangeActiveRoleViewSet, basename='change-active-role')
router.register(r'job-postings', JobPostingViewSet, basename='job-posting')
router.register(r'cvs', CVViewSet, basename='cv')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'ntd-profile', NtdProfileViewSet, basename='ntd-profile')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
]