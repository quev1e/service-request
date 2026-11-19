"""Регистрация, создание аккаунтов и другие операции"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, UpdateView

from .forms import (
    ResidentCreateForm,
    ResidentUpdateForm,
    SpecialistCreateForm,
    SpecialistUpdateForm,
    UserCreateForm,
    UserUpdateForm,
)
from .models import ResidentProfile, SpecialistProfile
from .mixins import UserMixin


class UserDetailView(
    UserMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    DetailView
):
    """Представление для просмотра 
    информации о пользователе и 
    связанных с ним заявок."""

    template_name = "users/user_detail.html"
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        """Добавляет в контекст заявки пользователя 
        с учётом его роли."""
        context = super().get_context_data(**kwargs)
        user = self.object

        if user.role == "Specialist":
            user_requests = user.taken_requests.all()
            context["requests_title"] = "Назначенные заявки"
        else:
            user_requests = user.requests.all()
            context["requests_title"] = "Созданные заявки"

        context["user_requests"] = (
            user_requests
            .select_related("category", "author", "specialist")
            .order_by("-date")
        )

        return context


class UserListView(
    UserMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    ListView
):
    """Представление для отображения 
    списка пользователей."""
    template_name = "users/user_list.html"
    context_object_name = 'users'


class UserUpdateView(
    UserMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):
    """Представление для редактирования 
    данных пользователей."""
    template_name = 'users/user_create_form.html'

    success_url = reverse_lazy('users:user_list')

    def get_form_class(self):
        """Выбирает форму редактирования в 
        зависимости от роли пользователя."""
        user = self.get_object()

        if user.role == 'Resident':
            return ResidentUpdateForm
        if user.role == 'Specialist':
            return SpecialistUpdateForm

        return UserUpdateForm

    def get_form_kwargs(self):
        """Передаёт профиль пользователя в 
        соответствующую форму редактирования."""
        kwargs = super().get_form_kwargs()
        user = self.get_object()

        if user.role == "Resident":
            kwargs[
                "profile"
            ] = ResidentProfile.objects.filter(user=user).first()
        elif user.role == "Specialist":
            kwargs[
                "profile"
            ] = SpecialistProfile.objects.filter(user=user).first()

        return kwargs


class UserCreateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    FormView
):
    """Базовое представление для создания 
    учётных записей администратором."""
    success_url = reverse_lazy('users:user_list')
    template_name = 'users/user_create_form.html'

    def test_func(self):
        """Проверяет, что текущий пользователь 
        имеет роль администратора."""
        return self.request.user.role == 'Administrator'

    def form_valid(self, form):
        """Сохраняет созданную учётную запись 
        после успешной проверки формы."""
        form.save()
        return super().form_valid(form)


class ResidentCreateView(UserCreateView):
    """Представление для создания учётной 
    записи проживающего."""
    form_class = ResidentCreateForm

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы 
        создания аккаунта проживающего."""
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт проживающего'
        return context


class SpecialistCreateView(UserCreateView):
    """Представление для создания учётной 
    записи специалиста."""
    form_class = SpecialistCreateForm

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы 
        создания аккаунта специалиста."""
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт специалиста'
        return context

class AdminCreateView(UserCreateView):
    """Представление для создания учётной 
    записи администратора."""
    form_class = UserCreateForm

    def get_context_data(self, **kwargs):
        """Добавляет заголовок страницы 
        создания аккаунта администратора."""
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт администратора'
        return context
