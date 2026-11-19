from django.contrib import admin

from .models import Attachment, Category, Request

admin.site.register(Request)
admin.site.register(Category)
admin.site.register(Attachment)
