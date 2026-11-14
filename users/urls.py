from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView
)
from django.urls import path, reverse_lazy
from .views import ResidentCreateView, SpecialistCreateView, UserListView, UserDetailView, AdminCreateView

app_name = 'users'


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_change/', PasswordChangeView.as_view(
        success_url=reverse_lazy("users:password_change_done")
        ),
        name='password_change'
    ),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('create_resident/', ResidentCreateView.as_view(), name='create_resident'),
    path('create_specialist/', SpecialistCreateView.as_view(), name='create_specialist'),
    path('create_administrator/', AdminCreateView.as_view(), name='create_admin'),
    path('user_list/', UserListView.as_view(), name='user_list'),
    path('user_detail/<int:pk>/', UserDetailView.as_view(), name='user_detail')
]