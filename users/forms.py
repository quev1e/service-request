"""Формы пользователей"""

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from requests.models import Category

from .models import ResidentProfile, SpecialistProfile, User
from .validators import contract_number_validator, room_number_validator


class UserCreateForm(forms.ModelForm):
    """Базовая форма создания пользователя с 
    проверкой и установкой пароля."""

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
        fields = [
            'username',
            'first_name',
            'last_name',
            'patronymic',
            'email',
            'phone'
        ]

    def clean(self):
        """Проверяет совпадение паролей и 
        соответствие пароля требованиям безопасности."""
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
        """Сохраняет пользователя с зашифрованным паролем."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class ResidentCreateForm(UserCreateForm):
    """Форма создания учётной записи 
    проживающего и его профиля."""

    contract_number = forms.CharField(
        max_length=13,
        label='Номер договора',
        validators=(contract_number_validator,)
    )
    room_number = forms.CharField(
        max_length=5,
        label='Номер комнаты',
        validators=(room_number_validator,)
    )

    @transaction.atomic
    def save(self, commit=True):
        """Создаёт пользователя с ролью проживающего 
        и связанный профиль."""
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
    """Форма создания учётной записи специалиста 
    с выбором категорий работ."""

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label='Категории',
        widget=forms.CheckboxSelectMultiple
    )

    def clean(self):
        """Проверяет, что для специалиста 
        выбрана хотя бы одна категория."""
        cleaned_data = super().clean()

        if not cleaned_data.get('categories'):
            self.add_error(
                'categories',
                'Выберите хотя бы одну категорию.'
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        """Создаёт пользователя с ролью специалиста 
        и назначает ему категории работ."""
        user = super().save(commit=False)
        user.role = "Specialist"

        if commit:
            user.save()
            specialist = SpecialistProfile.objects.create(user=user)
            specialist.categories.set(self.cleaned_data['categories'])
        return user


class UserUpdateForm(forms.ModelForm):
    """Базовая форма редактирования данных пользователя."""
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
    """Форма редактирования данных проживающего 
    и его профиля."""
    contract_number = forms.CharField(
        max_length=13,
        label="Номер договора",
        validators=(contract_number_validator,)
    )
    room_number = forms.CharField(
        max_length=5,
        label="Номер комнаты",
        validators=(room_number_validator,)
    )

    class Meta(UserUpdateForm.Meta):
        fields = UserUpdateForm.Meta.fields

    def __init__(self, *args, profile=None, **kwargs):
        """Инициализирует форму и заполняет поля данными 
        профиля проживающего."""
        super().__init__(*args, **kwargs)

        if profile:
            self.fields["contract_number"].initial = profile.contract_number
            self.fields["room_number"].initial = profile.room_number

    @transaction.atomic
    def save(self, commit=True):
        """Сохраняет данные пользователя и обновляет 
        или создаёт его профиль."""
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
    """Форма редактирования данных специалиста и 
    его категорий работ."""
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label="Категории",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserUpdateForm.Meta):
        fields = UserUpdateForm.Meta.fields

    def __init__(self, *args, profile=None, **kwargs):
        """Инициализирует форму и загружает текущие 
        категории специалиста."""
        super().__init__(*args, **kwargs)

        if profile:
            self.fields["categories"].initial = profile.categories.all()

    @transaction.atomic
    def save(self, commit=True):
        """Сохраняет данные пользователя и обновляет 
        его профиль и категории."""
        user = super().save(commit=False)

        if commit:
            user.save()

            profile, _ = SpecialistProfile.objects.get_or_create(
                user=user
            )
            profile.categories.set(self.cleaned_data["categories"])

        return user
    