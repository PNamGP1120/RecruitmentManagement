from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    RegistrationViewSet,
    LoginViewSet,
    NtvProfileViewSet,
    NtdRequestViewSet,
    ApproveNtdRequestViewSet,
    CVViewSet,
    UserAccountUpdateViewSet,
    JobPostingViewSet,
    NtdProfileViewSet, ApplicationViewSet
)

router = SimpleRouter()
router.register(r'register', RegistrationViewSet, basename='register')
router.register(r'auth', LoginViewSet, basename='auth')
router.register(r'ntv-profiles', NtvProfileViewSet, basename='ntv-profile')
router.register(r'ntd-requests', NtdRequestViewSet, basename='ntd-request')
router.register(r'approve-ntd-requests', ApproveNtdRequestViewSet, basename='approve-ntd-request')
router.register(r'cvs', CVViewSet, basename='cv')
router.register(r'users', UserAccountUpdateViewSet, basename='users')
router.register(r'job-postings', JobPostingViewSet, basename='job-posting')
router.register(r'ntd-profiles', NtdProfileViewSet, basename='ntd-profile') # Loại bỏ dòng trùng lặp
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginViewSet.as_view({'post': 'create'}), name='login-login'),
    path('users/me/', UserAccountUpdateViewSet.as_view({'put': 'update'}), name='user-account-update'),
    # URL cho action 'update_me' (nếu bạn muốn NTD tự cập nhật bằng '/me/')
    path('ntd-profiles/me/', NtdProfileViewSet.as_view({'put': 'update_me'}), name='ntd-profile-update-me'),
]