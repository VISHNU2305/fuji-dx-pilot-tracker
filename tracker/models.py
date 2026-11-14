from django.conf import settings
from django.db import models


class Business(models.Model):
    """One of the businesses the DX team supports (railway, hotel, park...)."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "businesses"

    def __str__(self):
        return self.name


class Problem(models.Model):
    """A problem reported by frontline staff."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        TRIAGED = "triaged", "Triaged"
        IN_PILOT = "in_pilot", "In pilot"
        RESOLVED = "resolved", "Resolved"

    business = models.ForeignKey(Business, on_delete=models.PROTECT,
                                 related_name="problems")
    title = models.CharField(max_length=150)
    description = models.TextField()
    workflow = models.TextField(
        help_text="The current steps, step by step, as the person does them.")
    times_per_month = models.PositiveIntegerField()
    minutes_per_time = models.PositiveIntegerField()
    people_affected = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.NEW)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT,
                                    related_name="reported_problems")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(times_per_month__gte=1),
                name="problem_times_per_month_at_least_1"),
            models.CheckConstraint(
                condition=models.Q(minutes_per_time__gte=1),
                name="problem_minutes_per_time_at_least_1"),
            models.CheckConstraint(
                condition=models.Q(people_affected__gte=1),
                name="problem_people_affected_at_least_1"),
        ]

    @property
    def hours_lost_per_month(self):
        """Hours lost each month = times per month x minutes each time / 60."""
        return self.times_per_month * self.minutes_per_time / 60

    def __str__(self):
        return f"{self.business}: {self.title}"