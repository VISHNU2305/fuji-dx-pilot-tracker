from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .effect import hours_saved_per_month, improvement_percent, pilot_effect
from .models import Business, Pilot, PilotResult, Problem

pytestmark = pytest.mark.django_db


@pytest.fixture
def problem():
    hotel = Business.objects.create(name="Hotels")
    user = User.objects.create_user("frontline1", password="pw-12345-test")
    return Problem.objects.create(
        business=hotel, title="Slow report", description="d", workflow="w",
        times_per_month=22, minutes_per_time=60, people_affected=2,
        reported_by=user)


@pytest.fixture
def planner():
    return User.objects.create_user("planner1", password="pw-12345-test")


def running_pilot(problem, planner, unit="minutes", baseline="60"):
    return Pilot.objects.create(
        problem=problem, owner=planner, goal="Cut report time",
        metric_name="Minutes per report", unit=unit,
        baseline_value=Decimal(baseline), target_value=Decimal("20"),
        measurement_method="Timed on 5 different days", status="running")


def add_result(pilot, user, value, on=date(2026, 12, 15),
               method="Timed on 5 days after the change"):
    return PilotResult.objects.create(
        pilot=pilot, value=Decimal(value), measured_on=on,
        method_note=method, recorded_by=user)


# Each row was worked out by hand first:
# hours saved = (minutes before - minutes after) x times per month / 60
# improvement = (before - after) / before x 100
@pytest.mark.parametrize("before, after, times, hours, percent", [
    (60, 20, 22, "14.7", "66.7"),   # 40 x 22 / 60 = 14.67 ; 40 / 60 = 66.67 %
    (45, 15, 10, "5.0", "66.7"),    # 30 x 10 / 60 = 5.0   ; 30 / 45 = 66.67 %
    (30, 30, 20, "0.0", "0.0"),     # nothing changed
    (20, 25, 22, "-1.8", "-25.0"),  # it got worse
])
def test_hours_saved_and_improvement_match_the_hand_calculation(
        before, after, times, hours, percent):
    assert hours_saved_per_month(before, after, times) == Decimal(hours)
    assert improvement_percent(before, after) == Decimal(percent)


def test_a_zero_baseline_cannot_give_a_percentage():
    with pytest.raises(ValueError):
        improvement_percent(0, 5)


def test_pilot_effect_matches_the_hand_calculation(problem, planner):
    pilot = running_pilot(problem, planner)
    add_result(pilot, planner, "20")
    effect = pilot_effect(pilot)
    assert effect["hours_saved_per_month"] == Decimal("14.7")
    assert effect["improvement_percent"] == Decimal("66.7")
    assert effect["method"] == "Timed on 5 days after the change"


def test_the_latest_result_is_the_one_used(problem, planner):
    pilot = running_pilot(problem, planner)
    add_result(pilot, planner, "30", on=date(2026, 12, 8))
    add_result(pilot, planner, "20", on=date(2026, 12, 15))
    assert pilot_effect(pilot)["result"] == Decimal("20.00")


def test_no_effect_can_be_given_before_a_result_exists(problem, planner):
    with pytest.raises(ValidationError):
        pilot_effect(running_pilot(problem, planner))


def test_hours_saved_needs_a_metric_measured_in_minutes(problem, planner):
    pilot = running_pilot(problem, planner, unit="errors")
    add_result(pilot, planner, "2")
    with pytest.raises(ValidationError):
        pilot_effect(pilot)


def test_the_database_refuses_a_result_without_a_method(problem, planner):
    pilot = running_pilot(problem, planner)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            add_result(pilot, planner, "20", method="")


def test_the_database_refuses_a_negative_result(problem, planner):
    pilot = running_pilot(problem, planner)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            add_result(pilot, planner, "-5")