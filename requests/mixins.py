"""Миксины для CBV заявок"""

from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

from .forms import RequestForm
from .models import Comment, Request


class RequestMixin:
    """Общие настройки представлений 
    для работы с заявками."""
    model = Request
    template_name = 'service_requests/request_form.html'
    success_url = reverse_lazy('requests:index')
    form_class = RequestForm


class CommentMixin:
    """Общая логика представлений 
    для работы с комментариями заявки."""
    model = Comment

    def dispatch(self, request, *args, **kwargs):
        """Получает заявку, к которой относится 
        комментарий, перед обработкой запроса."""
        self.request_obj = get_object_or_404(
            Request,
            pk=kwargs["request_pk"],
        )

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Возвращает адрес страницы заявки 
        после выполнения операции."""
        return reverse(
            "requests:detail",
            kwargs={"pk": self.request_obj.pk},
        )

    def get_context_data(self, **kwargs):
        """Добавляет объект заявки в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["request_obj"] = self.request_obj
        return context

    def get_queryset(self):
        """Возвращает комментарии только 
        для текущей заявки."""
        return Comment.objects.filter(
            request=self.request_obj
        )
