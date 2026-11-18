from .forms import RequestForm
from .models import Request, Comment, Attachment
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404


class RequestMixin:
    model = Request
    template_name = 'service_requests/request_form.html'
    success_url = reverse_lazy('requests:index')
    form_class = RequestForm


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

    def get_queryset(self):
        return Comment.objects.filter(
            request=self.request_obj
        )