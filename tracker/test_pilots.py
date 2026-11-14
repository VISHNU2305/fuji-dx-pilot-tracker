from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Business, Pilot, Problem

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


def complete_pilot(problem, planner, **extra):
    data = dict(problem=problem, owner=planner,
                goal="Cut report time to 20 minutes",
                metric_name="Minutes per report", unit="minutes",
                baseline_value=Decimal("60"), target_value=Decimal("20"),
                measurement_method="Timed on 5 different days")
    data.update(extra)
    return Pilot.objects.create(**data)


def test_a_new_pilot_is_a_draft(problem, planner):
    assert complete_pilot(problem, planner).status == "draft"


def test_a_draft_may_be_incomplete(problem, planner):
    pilot = Pilot.objects.create(problem=problem, owner=planner, goal="Idea only")
    assert pilot.status == "draft"


@pytest.mark.parametrize("missing", [
    {"baseline_value": None},
    {"target_value": None},
    {"metric_name": ""},
    {"measurement_method": ""},
])
def test_pilot_cannot_start_without_a_metric_baseline_target_or_method(
        problem, planner, missing):
    pilot = complete_pilot(problem, planner, **missing)
    with pytest.raises(ValidationError):
        pilot.start(date(2026, 12, 1))
    pilot.refresh_from_db()
    assert pilot.status == "draft"


def test_a_complete_pilot_can_start(problem, planner):
    pilot = complete_pilot(problem, planner)
    pilot.start(date(2026, 12, 1))
    pilot.refresh_from_db()
    problem.refresh_from_db()
    assert pilot.status == "running"
    assert pilot.start_date == date(2026, 12, 1)
    assert problem.status == "in_pilot"


def test_the_database_itself_refuses_a_running_pilot_without_a_baseline(
        problem, planner):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Pilot.objects.create(
                problem=problem, owner=planner, goal="Skip the rule",
                metric_name="Minutes", unit="minutes",
                target_value=Decimal("20"), measurement_method="Timed",
                baseline_value=None, status="running")