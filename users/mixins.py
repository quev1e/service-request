"""Миксин для CBV пользователя"""
from .models import User


class UserMixin:
    """Общий миксин для представлений, 
    работающих с пользователями."""
    model = User

    def test_func(self):
        """Проверяет, что текущий пользователь 
        имеет роль администратора."""
        return self.request.user.role == 'Administrator'
