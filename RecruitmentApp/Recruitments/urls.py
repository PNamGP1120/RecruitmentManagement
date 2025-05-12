from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegistrationView, LoginView, UpdateNtvProfileView, CreateNtdProfileView, AdminApproveNtdProfileView, \
    AdminAssignAdminRoleView, UserRolesView, ChangeRoleView, \
    CurrentUserView, UpdateUserProfileView, CVViewSet, JobPostingViewSet, ApplicationViewSet, InterviewViewSet, \
    MessageViewSet, AllConversationsView

router = DefaultRouter()
router.register(r'cvs', CVViewSet, basename='cv')
router.register(r'job-postings', JobPostingViewSet, basename='job-posting')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),

    # Job Postings
    path('job-postings/<uuid:pk>/approve/', JobPostingViewSet.as_view({'post': 'approve'}), name='approve-job-posting'),
    path('job-postings/<uuid:id>/request_approval/', JobPostingViewSet.as_view({'post': 'request_approval'}),
         name='request-approval-job-posting'),
    path('job-postings/<slug:pk>/', JobPostingViewSet.as_view({'get': 'retrieve_by_slug_or_uuid'}),
         name='retrieve-job-posting'),

    # CV
    path('cvs/<int:pk>/set_default/', CVViewSet.as_view({'post': 'set_default'}), name='cv-set-default'),

    # Applications (Đơn ứng tuyển)
    path('applications/', ApplicationViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='applications-list-create'),
    path('applications/<uuid:pk>/',
         ApplicationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='application-detail'),
    path('conversations/', AllConversationsView.as_view(), name='all_conversations'),

    # Other User Management APIs
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('create-ntv-profile/', UpdateNtvProfileView.as_view(), name='update_ntv_profile'),
    path('create-ntd-profile/', CreateNtdProfileView.as_view(), name='create-ntd-profile'),
    path('admin/approve-ntd-profile/', AdminApproveNtdProfileView.as_view(), name='approve-ntd-profile'),
    path('admin/assign-admin/', AdminAssignAdminRoleView.as_view(), name='admin-assign-admin'),
    path('user/roles/', UserRolesView.as_view(), name='user_roles'),
    path('change-role/', ChangeRoleView.as_view(), name='change_role'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('profile/update/', UpdateUserProfileView.as_view(), name='update-profile'),
]
