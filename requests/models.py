from django.db import models
from django.contrib.auth import get_user_model
from users.models import ResidentProfile

User = get_user_model()


class Category(models.Model):

    CATEGORIES = [
        ('Plumbing', 'Сантехника'),
        ('Electrical', 'Электрика'),
        ('Household', 'Хозяйственные работы')
    ]

    name = models.CharField(
        choices=CATEGORIES
    )


class Request(models.Model):

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
        default='New'
    )

    specialist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taken_requests",
        limit_choices_to={"role": "Specialist"}
    )


class Comment(models.Model):

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


class Attachment(models.Model):

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