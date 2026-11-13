from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView
)
from django.urls import path, reverse_lazy

app_name = 'users'


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_change/', PasswordChangeView.as_view(
        success_url=reverse_lazy("users:password_change_done")
    ), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done')
]