from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ResidentCreateForm, SpecialistCreateForm, UserCreateForm, UserUpdateForm, SpecialistUpdateForm, ResidentUpdateForm
from .models import User

class UserMixin:
    model = User
    
    def test_func(self):
        return self.request.user.role == 'Administrator'


class UserDetailView(UserMixin, LoginRequiredMixin, UserPassesTestMixin, DetailView):

    template_name = "users/user_detail.html"
    context_object_name = 'user'


class UserListView(UserMixin, LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "users/user_list.html"
    context_object_name = 'users'


class UserUpdateView(UserMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'users/user_create_form.html'
    
    success_url = reverse_lazy('users:user_list')
    
    def get_form_class(self):
        user = self.get_object()

        if user.role == 'Resident':
            return ResidentUpdateForm
        if user.role == 'Specialist':
            return SpecialistUpdateForm

        return UserUpdateForm


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    success_url = reverse_lazy('users:user_list')
    template_name = 'users/user_create_form.html'

    def test_func(self):
        return self.request.user.role == 'Administrator'

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ResidentCreateView(UserCreateView):
    form_class = ResidentCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт проживающего'
        return context



class SpecialistCreateView(UserCreateView):
    form_class = SpecialistCreateForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт специалиста'
        return context

class AdminCreateView(UserCreateView):
    form_class = UserCreateForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Создать аккаунт администратора'
        return context
    

