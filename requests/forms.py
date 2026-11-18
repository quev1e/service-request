
from django import forms
from .models import Request, Attachment, Comment
from .validators import attachment_validators
from django.db import transaction


class AttachmentModelForm(forms.ModelForm):
    """Общая форма для работы с вложениями."""

    file1 = forms.FileField(
        required=False,
        label="Вложение 1",
        widget=forms.ClearableFileInput,
        validators=attachment_validators
    )
    file2 = forms.FileField(
        required=False,
        label="Вложение 2",
        widget=forms.ClearableFileInput,
        validators=attachment_validators
    )
    file3 = forms.FileField(
        required=False,
        label="Вложение 3",
        widget=forms.ClearableFileInput,
        validators=attachment_validators
    )

    file_fields = ("file1", "file2", "file3")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.file_fields:
            self.fields[field_name].widget.attrs["class"] = "file-input"

    def save_attachments(self, request_obj, comment_obj=None):
        """Сохраняет загруженные файлы для заявки или комментария."""

        for field_name in self.file_fields:
            file = self.cleaned_data.get(field_name)

            if file:
                Attachment.objects.create(
                    request=request_obj,
                    file=file,
                    comment=comment_obj
                )


class RequestForm(AttachmentModelForm):

    class Meta:
        model = Request
        fields = ['category', 'description']
        
    @transaction.atomic
    def save(self, commit=True):
        request_obj = super().save(commit=False)

        if commit:
            request_obj.save()
            self.save_attachments(request_obj)

        return request_obj


class CommentForm(AttachmentModelForm):

    class Meta:
        model = Comment
        fields = ["text"]

        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Напишите комментарий",
                }
            )
        }

    @transaction.atomic
    def save(self, commit=True):
        comment_obj = super().save(commit=False)

        if commit:
            comment_obj.save()
            self.save_attachments(
                comment_obj.request,
                comment_obj
            )

        return comment_obj
