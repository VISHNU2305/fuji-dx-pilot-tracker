from django.contrib import admin

from .models import Business, Pilot, PilotResult, Problem

admin.site.register(Business)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "status", "reported_by", "created_at")
    list_filter = ("business", "status")


@admin.register(Pilot)
class PilotAdmin(admin.ModelAdmin):
    list_display = ("goal", "problem", "status", "owner", "start_date")
    list_filter = ("status",)


@admin.register(PilotResult)
class PilotResultAdmin(admin.ModelAdmin):
    list_display = ("pilot", "value", "measured_on", "recorded_by")