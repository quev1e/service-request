from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ResidentCreateForm, SpecialistCreateForm, UserCreateForm
from .models import User


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = 'user'

    def test_func(self):
        return self.request.user.role == 'Administrator'

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.role == 'Administrator'



class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    success_url = reverse_lazy('requests:index')
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
    

