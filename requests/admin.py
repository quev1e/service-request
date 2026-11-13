from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Request, Category, Attachment


admin.site.register(Request)
admin.site.register(Category)
admin.site.register(Attachment)