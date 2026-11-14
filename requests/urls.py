from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    index,
    RequestCreateView,
    RequestDetailView,
    take_request,
    change_status,
    CommentCreateView,
    RequestUpdateView,
    RequestDeleteView,
    CommentDeleteView,
    CommentUpdateView
)


app_name = 'requests'


urlpatterns = [
    path('', index, name='index'),
    path('requests/create/', RequestCreateView.as_view(), name='create'),
    path('requests/<int:pk>/', RequestDetailView.as_view(), name='detail'),
    path('requests/<int:pk>/edit/', RequestUpdateView.as_view(), name='request-update'),
    path('requests/<int:pk>/delete/', RequestDeleteView.as_view(), name='request-delete'),
    path('requests/take/<int:pk>/', take_request, name='take'),
    path('requests/update_status/<int:pk>/', change_status, name='update_status'),
    path('requests/<int:request_pk>/comments/add/', CommentCreateView.as_view(), name='add_comment'),
    path('requests/<int:request_pk>/comments/<int:pk>/edit/', CommentUpdateView.as_view(), name='comment-update'),
    path('requests/<int:request_pk>/comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)