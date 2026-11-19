"""Модели заявок, комментариев, вложений"""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Category(models.Model):
    """Категория заявки, определяющая тип необходимых работ."""

    CATEGORIES = [
        ('Plumbing', 'Сантехника'),
        ('Electrical', 'Электрика'),
        ('Household', 'Хозяйственные работы')
    ]

    name = models.CharField(
        choices=CATEGORIES,
        max_length=32
    )

    def __str__(self):
        """Возвращает отображаемое название категории."""
        return self.get_name_display()


class Request(models.Model):
    """Заявка жильца на выполнение работ в общежитии."""

    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    description = models.CharField(
        max_length=1024
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    STATUSES = [
        ('New', 'Новая'),
        ('In progress', 'В работе'),
        ('Completed', 'Выполнена'),
    ]

    status = models.CharField(
        choices=STATUSES,
        default='New',
        max_length=16
    )

    specialist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taken_requests",
        limit_choices_to={"role": "Specialist"}
    )

    def __str__(self):
        """Возвращает идентификатор заявки."""
        return f"Request No {self.pk}"


class Comment(models.Model):
    """Комментарий к заявке с возможностью создания ответов."""
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='comments'
    )

    text = models.TextField()

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True
    )

    def __str__(self):
        """Возвращает идентификатор комментария."""
        return f"Comment No {self.pk}"


class Attachment(models.Model):
    """Файл, прикреплённый непосредственно к заявке или комментарию."""

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(
        upload_to='attachments/'
    )

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachments',
        blank=True,
        null=True
    )

    @property
    def is_image(self):
        """
        Проверяет, относится ли файл к 
        поддерживаемым форматам изображений.
        """
        name = self.file.name.lower()
        return name.endswith((".jpg", ".jpeg", ".png", ".webp"))

    @property
    def is_video(self):
        """
        Проверяет, относится ли файл
        к поддерживаемым форматам видео.
        """
        name = self.file.name.lower()
        return name.endswith((".mp4", ".mov", ".webm"))


    def __str__(self):
        """Возвращает путь к прикреплённому файлу."""
        return self.file.name
