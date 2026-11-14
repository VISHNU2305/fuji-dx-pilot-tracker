from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q


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


class Pilot(models.Model):
    """A small-scale trial of an improvement for one problem."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        APPROVED = "approved", "Approved"
        RUNNING = "running", "Running"
        FINISHED = "finished", "Finished"

    problem = models.ForeignKey(Problem, on_delete=models.PROTECT,
                                related_name="pilots")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name="owned_pilots")
    goal = models.CharField(max_length=200)
    metric_name = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    baseline_value = models.DecimalField(max_digits=12, decimal_places=2,
                                         null=True, blank=True)
    target_value = models.DecimalField(max_digits=12, decimal_places=2,
                                       null=True, blank=True)
    measurement_method = models.TextField(
        blank=True, help_text="How the baseline and results are measured.")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Only a draft or a pilot in review may be incomplete.
            models.CheckConstraint(
                name="pilot_needs_metric_baseline_target_and_method",
                condition=(
                    Q(status__in=["draft", "review"])
                    | (~Q(metric_name="")
                       & Q(baseline_value__isnull=False)
                       & Q(target_value__isnull=False)
                       & ~Q(measurement_method=""))
                ),
            ),
            models.CheckConstraint(
                name="pilot_end_not_before_start",
                condition=(Q(start_date__isnull=True) | Q(end_date__isnull=True)
                           | Q(end_date__gte=F("start_date"))),
            ),
        ]

    def missing_for_start(self):
        missing = []
        if not self.metric_name:
            missing.append("a metric")
        if self.baseline_value is None:
            missing.append("a baseline")
        if self.target_value is None:
            missing.append("a target")
        if not self.measurement_method:
            missing.append("a measurement method")
        return missing

    def start(self, on):
        """Start the pilot, but only if it can be judged afterwards."""
        missing = self.missing_for_start()
        if missing:
            raise ValidationError(
                "A pilot cannot start without " + ", ".join(missing) + ".")
        with transaction.atomic():
            self.status = self.Status.RUNNING
            self.start_date = on
            self.save()
            self.problem.status = Problem.Status.IN_PILOT
            self.problem.save(update_fields=["status"])

    def __str__(self):
        return self.goal

    

class PilotResult(models.Model):
    """A value measured during or after a pilot, with how it was measured."""
    pilot = models.ForeignKey(Pilot, on_delete=models.PROTECT,
                              related_name="results")
    value = models.DecimalField(max_digits=12, decimal_places=2)
    measured_on = models.DateField()
    method_note = models.TextField(help_text="How this value was measured.")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT,
                                    related_name="recorded_results")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(name="result_value_not_negative",
                                   condition=Q(value__gte=0)),
            models.CheckConstraint(name="result_needs_a_method_note",
                                   condition=~Q(method_note="")),
        ]

    def __str__(self):
        return f"{self.pilot}: {self.value} on {self.measured_on}"