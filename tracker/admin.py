from django.contrib import admin

from .models import Business, Problem

admin.site.register(Business)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "status", "reported_by", "created_at")
    list_filter = ("business", "status")