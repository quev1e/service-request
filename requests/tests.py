"""Тесты приложения requests"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import SpecialistProfile

from .models import Category, Comment, Request

User = get_user_model()


class RequestWorkflowTests(TestCase):
    """Проверки основных сценариев работы с заявками и комментариями."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт тестовые категории, пользователей, 
        профили специалистов и заявки."""
        cls.plumbing = Category.objects.create(name="Plumbing")
        cls.electrical = Category.objects.create(name="Electrical")

        cls.resident = cls.create_user(
            "resident", "Resident", "resident@example.com"
        )
        cls.another_resident = cls.create_user(
            "resident2", "Resident", "resident2@example.com"
        )
        cls.specialist = cls.create_user(
            "specialist", "Specialist", "specialist@example.com"
        )
        cls.other_specialist = cls.create_user(
            "specialist2", "Specialist", "specialist2@example.com"
        )
        cls.admin = cls.create_user(
            "admin", "Administrator", "admin@example.com"
        )

        cls.specialist_profile = SpecialistProfile.objects.create(
            user=cls.specialist
        )
        cls.specialist_profile.categories.add(cls.plumbing)

        cls.other_specialist_profile = SpecialistProfile.objects.create(
            user=cls.other_specialist
        )
        cls.other_specialist_profile.categories.add(cls.electrical)

        cls.resident_request = Request.objects.create(
            author=cls.resident,
            category=cls.plumbing,
            description="Течёт кран",
        )
        cls.other_request = Request.objects.create(
            author=cls.another_resident,
            category=cls.electrical,
            description="Не работает свет",
        )

    @staticmethod
    def create_user(username, role, email):
        """Создаёт тестового пользователя с указанными 
        учётными данными и ролью."""
        return User.objects.create_user(
            username=username,
            password="StrongTestPassword123!",
            first_name="Тест",
            last_name="Пользователь",
            email=email,
            phone="12345678901",
            role=role,
        )

    def login(self, user):
        """Выполняет авторизацию тестового пользователя."""
        self.client.force_login(user)

    # Главная страница и списки заявок

    def test_resident_sees_only_own_requests_on_index(self):
        self.login(self.resident)

        response = self.client.get(reverse("requests:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["requests"]),
            [self.resident_request],
        )

    def test_administrator_sees_all_requests_on_index(self):
        self.login(self.admin)

        response = self.client.get(reverse("requests:index"))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.context["requests"],
            [self.resident_request, self.other_request],
        )

    def test_specialist_sees_only_requests_of_own_categories(self):
        self.login(self.specialist)

        response = self.client.get(reverse("requests:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["requests"]),
            [self.resident_request],
        )

    def test_specialist_can_filter_requests_by_status(self):
        self.resident_request.status = "In progress"
        self.resident_request.specialist = self.specialist
        self.resident_request.save()
        self.login(self.specialist)

        response = self.client.get(
            reverse("requests:index"),
            {"status": "New"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["requests"]), [])

    # Просмотр заявки и разграничение доступа

    def test_resident_can_open_own_request(self):
        self.login(self.resident)

        response = self.client.get(
            reverse("requests:detail", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_resident_cannot_open_another_residents_request(self):
        self.login(self.resident)

        response = self.client.get(
            reverse("requests:detail", args=[self.other_request.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_specialist_can_open_request_of_own_category(self):
        self.login(self.specialist)

        response = self.client.get(
            reverse("requests:detail", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_specialist_cannot_open_request_of_another_category(self):
        self.login(self.specialist)

        response = self.client.get(
            reverse("requests:detail", args=[self.other_request.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("requests:detail", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    # Создание заявок

    def test_resident_can_create_request(self):
        self.login(self.resident)

        response = self.client.post(
            reverse("requests:create"),
            {
                "category": self.plumbing.pk,
                "description": "Нужно починить раковину",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Request.objects.filter(
                author=self.resident,
                category=self.plumbing,
                description="Нужно починить раковину",
            ).exists()
        )

    def test_specialist_cannot_create_request(self):
        self.login(self.specialist)

        response = self.client.get(reverse("requests:create"))

        self.assertEqual(response.status_code, 403)

    # Взятие заявки специалистом

    def test_specialist_can_take_request_of_own_category(self):
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:take", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.resident_request.refresh_from_db()
        self.assertEqual(self.resident_request.specialist, self.specialist)
        self.assertEqual(self.resident_request.status, "In progress")

    def test_specialist_cannot_take_request_outside_own_category(self):
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:take", args=[self.other_request.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.other_request.refresh_from_db()
        self.assertIsNone(self.other_request.specialist)
        self.assertEqual(self.other_request.status, "New")

    def test_resident_cannot_take_request(self):
        self.login(self.resident)

        response = self.client.post(
            reverse("requests:take", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_request_cannot_be_taken_twice(self):
        self.resident_request.specialist = self.specialist
        self.resident_request.status = "In progress"
        self.resident_request.save()
        self.login(self.other_specialist)

        response = self.client.post(
            reverse("requests:take", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 403)

    # Изменение статуса

    def test_assigned_specialist_can_change_status_to_completed(self):
        self.resident_request.specialist = self.specialist
        self.resident_request.status = "In progress"
        self.resident_request.save()
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:update_status", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.resident_request.refresh_from_db()
        self.assertEqual(self.resident_request.status, "Completed")

    def test_specialist_cannot_change_status_of_unassigned_request(self):
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:update_status", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.resident_request.refresh_from_db()
        self.assertEqual(self.resident_request.status, "New")

    def test_completed_request_status_cannot_be_changed_again(self):
        self.resident_request.specialist = self.specialist
        self.resident_request.status = "Completed"
        self.resident_request.save()
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:update_status", args=[self.resident_request.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.resident_request.refresh_from_db()
        self.assertEqual(self.resident_request.status, "Completed")

    # Комментарии

    def test_request_author_can_add_comment(self):
        self.login(self.resident)

        response = self.client.post(
            reverse("requests:add_comment", args=[self.resident_request.pk]),
            {"text": "Когда придёт специалист?"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(
                request=self.resident_request,
                author=self.resident,
                text="Когда придёт специалист?",
            ).exists()
        )

    def test_assigned_specialist_can_add_comment(self):
        self.resident_request.specialist = self.specialist
        self.resident_request.status = "In progress"
        self.resident_request.save()
        self.login(self.specialist)

        response = self.client.post(
            reverse("requests:add_comment", args=[self.resident_request.pk]),
            {"text": "Заявка принята в работу"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(
                request=self.resident_request,
                author=self.specialist,
            ).exists()
        )

    def test_unrelated_user_cannot_add_comment(self):
        self.login(self.another_resident)

        response = self.client.post(
            reverse("requests:add_comment", args=[self.resident_request.pk]),
            {"text": "Посторонний комментарий"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Comment.objects.filter(text="Посторонний комментарий").exists()
        )

    def test_comment_can_be_added_as_reply_to_comment_of_same_request(self):
        parent = Comment.objects.create(
            request=self.resident_request,
            author=self.resident,
            text="Первый комментарий",
        )
        self.login(self.resident)

        response = self.client.post(
            reverse("requests:add_comment", args=[self.resident_request.pk]),
            {"text": "Ответ на комментарий", "parent_id": parent.pk},
        )

        self.assertEqual(response.status_code, 302)
        reply = Comment.objects.get(text="Ответ на комментарий")
        self.assertEqual(reply.parent, parent)
        self.assertEqual(reply.request, self.resident_request)

    def test_cannot_reply_to_comment_from_another_request(self):
        parent = Comment.objects.create(
            request=self.other_request,
            author=self.another_resident,
            text="Комментарий к другой заявке",
        )
        self.login(self.resident)

        response = self.client.post(
            reverse("requests:add_comment", args=[self.resident_request.pk]),
            {"text": "Попытка ответа", "parent_id": parent.pk},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Comment.objects.filter(text="Попытка ответа").exists()
        )

    def test_comment_author_can_edit_own_comment(self):
        comment = Comment.objects.create(
            request=self.resident_request,
            author=self.resident,
            text="Старый текст",
        )
        self.login(self.resident)

        response = self.client.post(
            reverse(
                "requests:comment-update",
                args=[self.resident_request.pk, comment.pk],
            ),
            {"text": "Изменённый текст"},
        )

        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.text, "Изменённый текст")

    def test_user_cannot_edit_another_users_comment(self):
        comment = Comment.objects.create(
            request=self.resident_request,
            author=self.specialist,
            text="Комментарий специалиста",
        )
        self.login(self.resident)

        response = self.client.get(
            reverse(
                "requests:comment-update",
                args=[self.resident_request.pk, comment.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_user_cannot_edit_comment_from_another_request(self):
        comment = Comment.objects.create(
            request=self.other_request,
            author=self.resident,
            text="Комментарий к другой заявке",
        )
        self.login(self.resident)

        response = self.client.get(
            reverse(
                "requests:comment-update",
                args=[self.resident_request.pk, comment.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
