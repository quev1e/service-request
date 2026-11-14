from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Request, Comment
from .forms import RequestForm, CommentForm



@login_required
def index(request):

    templates = {
        'Resident': 'home/resident.html',
        'Specialist': 'home/specialist.html',
        'Administrator': 'home/administrator.html'
    }

    role = request.user.role
    template_name = templates.get(request.user.role)

    if not template_name:
        raise PermissionDenied("Для пользователя не определена роль.")

    if role == 'Administrator':
        return render(request, template_name)

    if role == 'Resident':
        requests = Request.objects.filter(author=request.user)

        context = {
            'requests': requests,
            'user': request.user
        }
        return render(request, template_name, context)

    if role == 'Specialist':
        specialist_categories = request.user.specialist.categories.all()
        
        status = request.GET.get("status")
        category_id = request.GET.get("category")
        specialist_id = request.GET.get("specialist")
        
        requests = Request.objects.filter(category__in=specialist_categories).order_by("-date")
        
        if specialist_id:
            requests = requests.filter(specialist_id=specialist_id)
        
        if status:
            requests = requests.filter(status=status)

        if category_id:
            requests = requests.filter(category_id=category_id)

        context = {
            'requests': requests,
            'user': request.user,
            "selected_status": status or "",
            "selected_category": category_id or "",
            "selected_specialist": specialist_id or ""
        }

        return render(request, template_name, context)


class RequestMixin:
    model = Request
    template_name = 'service_requests/request_form.html'
    success_url = reverse_lazy('requests:index')
    form_class = RequestForm


class RequestCreateView(RequestMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):

    def test_func(self):
        return self.request.user.role == 'Resident'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class RequestUpdateView(RequestMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    def test_func(self):
        request = self.get_object()
        user = self.request.user

        return request.author == user and request.status == 'New'


class RequestDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    
    model = Request
    template_name = 'service_requests/request_confirm_delete.html'
    success_url = reverse_lazy('requests:index')

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class RequestDetailView(LoginRequiredMixin, DetailView):
    
    model = Request
    template_name = 'service_requests/request_detail.html'

    def get_object(self, queryset=None):

        obj = super().get_object(queryset)
        user = self.request.user

        if user.role == 'Resident' and user != obj.author:
            raise PermissionDenied("Нельзя просмотреть чужую заявку.")

        if user.role == 'Specialist' and obj.category not in user.specialist.categories.all():
            raise PermissionDenied("Нельзя просмотреть заявки из других категорий.")

        return obj

    def get_context_data(self, **kwargs):
        user = self.request.user
        request_obj = self.get_object()

        can_take = False
        can_change_status = False
        can_edit = False
        
        if request_obj.author == user:
            can_edit = True

        attachments = request_obj.attachments.filter(comment=None)
        if user.role == 'Specialist':
            if not request_obj.specialist:
                can_take = True
            if request_obj.specialist == user and request_obj.status != 'Completed':
                can_change_status = True

        can_comment = user in (request_obj.author, request_obj.specialist)

        comments = None
        comment_form = None
        if can_comment:
            comments = request_obj.comments.all()
            comment_form = CommentForm()

        return {
            "can_edit": can_edit,
            'can_take': can_take,
            'can_change_status': can_change_status,
            'can_comment': can_comment,
            'request_obj': request_obj,
            "attachments": attachments,
            "comments": comments,
            "comment_form": comment_form
        }


@login_required
def take_request(request, pk):

    obj = get_object_or_404(Request, pk=pk)
    user = request.user

    if request.method != 'POST':
        return redirect('requests:index')

    if user.role != 'Specialist':
        raise PermissionDenied('Только специалист может брать заявки.')

    categories = user.specialist.categories.all()

    if obj.category not in categories:
        raise PermissionDenied('Нельзя брать заявки не своей специализации.')

    if obj.status != 'New' or obj.specialist:
        raise PermissionDenied('Заявка уже взята')

    obj.specialist = user
    obj.status = 'In progress'
    obj.save()
    return redirect("requests:detail", pk=obj.pk)


@login_required
def change_status(request, pk):

    obj = get_object_or_404(Request, pk=pk)
    user = request.user

    if request.method != 'POST':
        return redirect('requests:index')

    if user.role != 'Specialist':
        raise PermissionDenied('Только специалист может изменять статус заявки.')

    if obj.specialist != user:
        raise PermissionDenied('Нельзя изменять статус чужой заявки.')

    if obj.status == 'Completed':
        raise PermissionDenied('Заявка уже выполнена.')

    if obj.status == 'New':
        obj.status = 'In progress'
    elif obj.status == 'In progress':
        obj.status = 'Completed'

    obj.save()
    return redirect("requests:detail", pk=obj.pk)


class CommentMixin:
    model = Comment

    def dispatch(self, request, *args, **kwargs):
        self.request_obj = get_object_or_404(
            Request,
            pk=kwargs["request_pk"],
        )

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "requests:detail",
            kwargs={"pk": self.request_obj.pk},
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request_obj"] = self.request_obj
        return context



class CommentCreateView(CommentMixin, LoginRequiredMixin, UserPassesTestMixin, CreateView):
    
    form_class = CommentForm
    template_name = 'service_requests/comment_form.html'

    def test_func(self):
        return self.request.user in (self.request_obj.author, self.request_obj.specialist)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.request = self.request_obj
        form.instance.parent = self.get_parent()
        return super().form_valid(form)

    def get_parent(self):
        parent_id = self.request.POST.get("parent_id")

        if not parent_id:
            return None

        return get_object_or_404(
            Comment,
            pk=parent_id,
            request=self.request_obj,
        )

class CommentUpdateView(CommentMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    
    form_class = CommentForm
    template_name = 'service_requests/comment_form.html'
    
    def test_func(self):
        comment = self.get_object()
        user = self.request.user

        return comment.author == user


class CommentDeleteView(CommentMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    
    template_name = 'service_requests/comment_delete_confirm.html'

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user

