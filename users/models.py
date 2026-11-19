"""Пользователи и профили"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import (
    contract_number_validator,
    phone_number_validator,
    room_number_validator,
)


class User(AbstractUser):
    """Модель пользователя с поддержкой 
    ролевого разграничения доступа."""

    ROLES = [
        ('Resident', 'Проживающий'),
        ('Specialist', 'Специалист'),
        ("Administrator", "Администратор")
    ]

    role = models.CharField(
        choices=ROLES,
        default='Administrator',
        verbose_name='Роль'
    )

    username = models.CharField(
        max_length=124,
        unique=True,
        verbose_name='Юзернейм'
    )

    first_name = models.CharField(
        max_length=124,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=124,
        verbose_name='Фамилия'
    )

    patronymic = models.CharField(
        max_length=124,
        blank=True,
        verbose_name='Отчество'
    )

    email = models.EmailField(
        unique=True,
        verbose_name='Емейл',
    )

    phone = models.CharField(
        max_length=12,
        validators = (phone_number_validator,),
        verbose_name='Номер телефона'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный пользователь'
    )

    def __str__(self):
        """Возвращает имя и фамилию пользователя."""
        return f"{self.last_name} {self.first_name}"


class ResidentProfile(models.Model):
    """Профиль проживающего с информацией 
    о договоре и комнате."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='resident',
        verbose_name='Пользователь'
    )

    contract_number = models.CharField(
        max_length=13,
        validators=(contract_number_validator,),
        verbose_name='Номер договора'
    )

    room_number = models.CharField(
        max_length=5,
        validators=(room_number_validator,),
        verbose_name='Номер комнаты'
    )

    def __str__(self):
        """Возвращает имя и фамилию проживающего."""
        return f"Resident {self.user.last_name} {self.user.first_name}"


class SpecialistProfile(models.Model):
    """Профиль специалиста с перечнем 
    доступных категорий работ."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='specialist',
        verbose_name='Пользователь'
    )

    categories = models.ManyToManyField(
        'requests.Category',
        related_name='specialists',
        verbose_name='Категории'
    )

    def __str__(self):
        """Возвращает имя и фамилию специалиста."""
        return f"Specialist {self.user.last_name} {self.user.first_name}"
