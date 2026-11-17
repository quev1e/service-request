from django import forms
from .models import User, ResidentProfile, SpecialistProfile
from requests.models import Category
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserCreateForm(forms.ModelForm):

    password1 = forms.CharField(
        max_length=20,
        label='Пароль',
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        max_length=20,
        label='Пароль',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'patronymic', 'email', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            self.add_error('password2', "Пароли не совпадают")

        if password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                self.add_error('password1', e)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class ResidentCreateForm(UserCreateForm):

    contract_number = forms.CharField(
        max_length=13,
        label='Номер договора'
    )
    room_number = forms.CharField(
        max_length=5,
        label='Номер комнаты'
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "Resident"

        if commit:
            user.save()
            ResidentProfile.objects.create(
                user=user,
                contract_number=self.cleaned_data["contract_number"],
                room_number=self.cleaned_data["room_number"]
            )
        return user


class SpecialistCreateForm(UserCreateForm):

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label='Категории',
        widget=forms.CheckboxSelectMultiple
    )

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('categories'):
            self.add_error(
                'categories',
                'Выберите хотя бы одну категорию.'
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "Specialist"

        if commit:
            user.save()
            specialist = SpecialistProfile.objects.create(user=user)
            specialist.categories.set(self.cleaned_data['categories'])
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'patronymic',
            'email',
            'phone',
            'is_active',
        ]


class ResidentUpdateForm(UserUpdateForm):
    contract_number = forms.CharField(
        max_length=13,
        label="Номер договора",
    )
    room_number = forms.CharField(
        max_length=5,
        label="Номер комнаты",
    )

    class Meta(UserUpdateForm.Meta):
        fields = UserUpdateForm.Meta.fields

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)

        if profile:
            self.fields["contract_number"].initial = profile.contract_number
            self.fields["room_number"].initial = profile.room_number

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            ResidentProfile.objects.update_or_create(
                user=user,
                defaults={
                    "contract_number": self.cleaned_data["contract_number"],
                    "room_number": self.cleaned_data["room_number"],
                },
            )

        return user


class SpecialistUpdateForm(UserUpdateForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label="Категории",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserUpdateForm.Meta):
        fields = UserUpdateForm.Meta.fields

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)

        if profile:
            self.fields["categories"].initial = profile.categories.all()

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            profile, created = SpecialistProfile.objects.get_or_create(
                user=user
            )
            profile.categories.set(self.cleaned_data["categories"])

        return user