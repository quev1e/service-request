from django import forms
from .models import Request, Attachment, Comment
from .validators import attachment_validators


class RequestForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in ("file1", "file2", "file3"):
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["class"] = "file-input"
    class Meta:
        model = Request

        fields = ['category', 'description']

    def save(self, commit=True):
        request_obj = super().save(commit=False)

        if commit:
            request_obj.save()

            uploaded_files = [self.cleaned_data.get(f"file{i}") for i in range (1,4)]
            for file in uploaded_files:
                if file:
                    Attachment.objects.create(
                        request=request_obj,
                        file=file
                    )
        return request_obj
    



class CommentForm(forms.ModelForm):

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

    def save(self, commit=True):
        comment_obj = super().save(commit=False)

        if commit:
            comment_obj.save()

            uploaded_files = [self.cleaned_data.get(f"file{i}") for i in range (1,4)]
            for file in uploaded_files:
                if file:
                    Attachment.objects.create(
                        request=comment_obj.request,
                        file=file,
                        comment=comment_obj
                    )
        return comment_obj
