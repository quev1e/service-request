from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLES = [
        ('Resident', 'Проживающий'),
        ('Specialist', 'Специалист'),
        ("Administrator", "Администратор")
    ]

    role = models.CharField(
        choices=ROLES,
        default='Resident'
    )

    username = models.CharField(
        max_length=124,
        unique=True
    )

    first_name = models.CharField(
        max_length=124
    )

    last_name = models.CharField(
        max_length=124
    )

    patronymic = models.CharField(
        max_length=124,
        blank=True
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=12,
        # validators = (phone_number,)
    )

    is_active = models.BooleanField(
        default=True
    )

    is_staff = models.BooleanField(
        default=False
    )


class ResidentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='resident'
    )

    contract_number = models.CharField(
        max_length=13,
        #validators=(contract_number_validator,)
    )

    room_number = models.CharField(
        max_length=5,
        #validators=(room_number_validator,)
    )


class SpecialistProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='specialist'
    )

    categories = models.ManyToManyField(
        'requests.Category',
        related_name='specialists'
    )