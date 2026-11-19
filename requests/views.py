"""Представления, обработчики, вспомогательные функции"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, IntegerField, Prefetch, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import CommentForm
from .mixins import CommentMixin, RequestMixin
from .models import Attachment, Comment, Request
from .utils import delete_attachments


def get_admin_requests():
    """Возвращает все заявки с загруженными 
    связанными объектами, отсортированные 
    по дате создания."""
    return Request.objects.select_related(
        'author',
        'category',
        'specialist'
    ).order_by('-date')


def get_resident_requests(user):
    """Возвращает заявки указанного жильца, 
    отсортированные по дате создания."""
    return Request.objects.filter(
        author=user
    ).select_related(
        'author',
        'category',
        'specialist'
    ).order_by('-date')


def get_specialist_requests(user, status='', category_id='', only_mine=''):
    """Возвращает заявки по категориям 
    специалиста с учётом фильтров и 
    приоритета обработки."""
    specialist_categories = user.specialist.categories.all()

    requests = Request.objects.filter(
        category__in=specialist_categories
    ).select_related(
        'author',
        'category',
        'specialist'
    )

    if status in ("New", "In progress", "Completed"):
        requests = requests.filter(status=status)

    if category_id:
        requests = requests.filter(category_id=category_id)

    if only_mine == "1":
        requests = requests.filter(specialist=user)

    return requests.annotate(
        priority=Case(
            When(
                status="In progress",
                specialist=user,
                then=Value(1),
            ),
            When(
                status="New",
                specialist__isnull=True,
                then=Value(2),
            ),
            default=Value(5),
            output_field=IntegerField(),
        )
    ).order_by("priority", "status", "-date")


@login_required
def index(request):
    """Отображает главную страницу 
    с заявками в зависимости от роли пользователя."""

    templates = {
        'Resident': 'home/resident.html',
        'Specialist': 'home/specialist.html',
        'Administrator': 'home/administrator.html'
    }

    user = request.user
    role = user.role

    template_name = templates.get(role)

    if not template_name:
        raise PermissionDenied("Для пользователя не определена роль.")

    context = {
        'user': user
    }

    if role == 'Administrator':
        context['requests'] = get_admin_requests()

    elif role == 'Resident':
        context['requests'] = get_resident_requests(user)

    elif role == 'Specialist':
        status = request.GET.get("status", "")
        category_id = request.GET.get("category", "")
        only_mine = request.GET.get("only_mine", "")

        specialist_categories = user.specialist.categories.all()

        context.update({
            'requests': get_specialist_requests(
                user,
                status,
                category_id,
                only_mine
            ),
            'specialist_categories': specialist_categories,
            'selected_status': status,
            'selected_category': category_id,
            'selected_only_mine': only_mine,
        })

    return render(request, template_name, context)

class RequestCreateView(
    RequestMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    CreateView
    ):
    """Представление для создания заявок жильцами."""

    def test_func(self):
        """Разрешает создание заявок только 
        пользователям с ролью жильца."""
        return self.request.user.role == 'Resident'

    def form_valid(self, form):
        """Назначает текущего пользователя 
        автором заявки перед сохранением."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class RequestUpdateView(
    RequestMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
    ):
    """Представление для редактирования заявок жильцами."""

    def test_func(self):
        """Проверяет, что пользователь является 
        автором новой заявки."""
        request = self.get_object()
        user = self.request.user

        return request.author == user and request.status == 'New'

    def get_context_data(self, **kwargs):
        """Добавляет вложения заявки в контекст шаблона."""
        context = super().get_context_data(**kwargs)

        context["attachments"] = self.object.attachments.filter(
            comment__isnull=True
        )

        return context

    def form_valid(self, form):
        """Сохраняет изменения заявки и 
        удаляет выбранные вложения."""
        response = super().form_valid(form)

        delete_attachments(
            self.object.attachments.filter(comment__isnull=True),
            self.request.POST
        )

        return response


class RequestDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    """Представление для удаления заявки её автором."""

    model = Request
    template_name = 'service_requests/request_confirm_delete.html'
    success_url = reverse_lazy('requests:index')

    def test_func(self):
        """Проверяет, что текущий пользователь 
        является автором заявки."""
        obj = self.get_object()
        return obj.author == self.request.user


class RequestDetailView(LoginRequiredMixin, DetailView):
    """Представление для просмотра подробной 
    информации о заявке."""

    model = Request
    template_name = 'service_requests/request_detail.html'

    def get_object(self, queryset=None):
        """Получает заявку и проверяет права 
        пользователя на её просмотр."""

        obj = super().get_object(queryset)
        user = self.request.user

        if user.role == 'Resident' and user != obj.author:
            raise PermissionDenied("Нельзя просмотреть чужую заявку.")

        if user.role == 'Specialist':
            has_access = user.specialist.categories.filter(
                pk=obj.category_id
            ).exists()

            if not has_access:
                raise PermissionDenied(
                    "Нельзя просмотреть заявки из других категорий."
                )

        return obj

    def get_queryset(self):
        """Оптимизирует получение заявки, комментариев, 
        вложений и связанных объектов."""
        reply_queryset = (
            Comment.objects
            .select_related("author")
            .prefetch_related("attachments")
        )

        comment_queryset = (
            Comment.objects
            .select_related("author")
            .prefetch_related(
                "attachments",
                Prefetch(
                    "replies",
                    queryset=reply_queryset
                )
            )
        )

        return (
            Request.objects
            .select_related(
                "author",
                "author__resident",
                "category",
                "specialist"
            )
            .prefetch_related(
                Prefetch(
                    "attachments",
                    queryset=Attachment.objects.filter(comment=None),
                    to_attr="request_attachments"
                ),
                Prefetch(
                    "comments",
                    queryset=comment_queryset,
                    to_attr="prefetched_comments"
                )
            )
        )

    def get_context_data(self, **kwargs):
        """Формирует контекст страницы с заявкой и 
        определяет доступные пользователю действия."""
        user = self.request.user
        request_obj = self.object

        can_take = False
        can_change_status = False
        can_edit = False

        if request_obj.author == user:
            can_edit = True

        attachments = request_obj.request_attachments

        if user.role == 'Specialist':
            if not request_obj.specialist:
                can_take = True

            if (
                request_obj.specialist == user
                and request_obj.status != 'Completed'
            ):
                can_change_status = True

        can_comment = user in (
            request_obj.author,
            request_obj.specialist
        )

        comments = None
        comment_form = None

        if can_comment:
            comments = request_obj.prefetched_comments
            comment_form = CommentForm()

        return {
            "can_edit": can_edit,
            "can_take": can_take,
            "can_change_status": can_change_status,
            "can_comment": can_comment,
            "request_obj": request_obj,
            "attachments": attachments,
            "comments": comments,
            "comment_form": comment_form,
            "user": user
        }


@login_required
def take_request(request, pk):
    """Назначает заявку специалисту с 
    проверкой категории и текущего статуса."""

    if request.method != 'POST':
        return redirect('requests:index')

    user = request.user

    if user.role != 'Specialist':
        raise PermissionDenied('Только специалист может брать заявки.')

    try:
        with transaction.atomic():
            obj = get_object_or_404(
                Request.objects.select_for_update(),
                pk=pk,
            )

            has_category = user.specialist.categories.filter(
                pk=obj.category_id
            ).exists()

            if not has_category:
                raise PermissionDenied(
                    "Нельзя брать заявки не своей специализации."
                )

            if obj.status != "New" or obj.specialist:
                raise PermissionDenied("Заявка уже взята.")

            obj.specialist = user
            obj.status = "In progress"
            obj.save()

    except PermissionDenied:
        raise

    return redirect("requests:detail", pk=obj.pk)


@login_required
def change_status(request, pk):
    """Изменяет статус заявки специалистом, 
    которому она назначена."""

    obj = get_object_or_404(Request, pk=pk)
    user = request.user

    if request.method != 'POST':
        return redirect('requests:index')

    if user.role != 'Specialist':
        raise PermissionDenied(
            'Только специалист может изменять статус заявки.'
        )

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


class CommentCreateView(
    LoginRequiredMixin,
    CommentMixin,
    UserPassesTestMixin,
    CreateView
):
    """Представление для создания комментариев и ответов к ним."""

    form_class = CommentForm
    template_name = 'service_requests/comment_form.html'

    def test_func(self):
        """Разрешает добавление комментариев автору 
        заявки и назначенному специалисту."""
        return self.request.user in (
            self.request_obj.author,
            self.request_obj.specialist
        )

    def form_valid(self, form):
        """Назначает автору и заявке соответствующие 
        объекты перед сохранением комментария."""
        form.instance.author = self.request.user
        form.instance.request = self.request_obj
        form.instance.parent = self.get_parent()
        return super().form_valid(form)

    def get_parent(self):
        """Получает родительский комментарий для 
        ответа в рамках текущей заявки."""
        parent_id = self.request.POST.get("parent_id")

        if not parent_id:
            return None

        return get_object_or_404(
            Comment,
            pk=parent_id,
            request=self.request_obj,
            parent__isnull=True,
        )

class CommentUpdateView(
    LoginRequiredMixin,
    CommentMixin,
    UserPassesTestMixin,
    UpdateView
):
    """Представление для редактирования 
    комментариев их авторами."""

    form_class = CommentForm
    template_name = 'service_requests/comment_form.html'

    def test_func(self):
        """Проверяет, что текущий пользователь 
        является автором комментария."""
        comment = self.get_object()
        user = self.request.user

        return comment.author == user

    def form_valid(self, form):
        """Сохраняет изменения комментария 
        и удаляет выбранные вложения."""
        response = super().form_valid(form)

        delete_attachments(
            self.object.attachments.all(),
            self.request.POST
        )

        return response


class CommentDeleteView(
    LoginRequiredMixin,
    CommentMixin,
    UserPassesTestMixin,
    DeleteView
):
    """Представление для удаления комментариев их авторами."""

    template_name = 'service_requests/comment_delete_confirm.html'

    def test_func(self):
        """Проверяет, что текущий пользователь 
        является автором комментария."""
        comment = self.get_object()
        return comment.author == self.request.user
