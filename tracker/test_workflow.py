from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError

from . import roles, workflow
from .models import Business, Pilot, PilotResult, Problem

pytestmark = pytest.mark.django_db


def make_user(name, group=None, superuser=False):
    user = User.objects.create_user(name, password="pw-12345-test",
                                    is_superuser=superuser)
    if group:
        user.groups.add(Group.objects.get_or_create(name=group)[0])
    return user


@pytest.fixture
def planner():
    return make_user("planner1", roles.PLANNER_GROUP)


@pytest.fixture
def manager():
    return make_user("manager1", roles.MANAGER_GROUP)


@pytest.fixture
def frontline():
    return make_user("frontline1")


@pytest.fixture
def problem(frontline):
    hotel = Business.objects.create(name="Hotels")
    return Problem.objects.create(
        business=hotel, title="Slow report", description="d", workflow="w",
        times_per_month=22, minutes_per_time=60, people_affected=2,
        reported_by=frontline)


def new_pilot(problem, owner, status="draft", **extra):
    data = dict(problem=problem, owner=owner,
                goal="Cut report time to 20 minutes",
                metric_name="Minutes per report", unit="minutes",
                baseline_value=Decimal("60"), target_value=Decimal("20"),
                measurement_method="Timed on 5 different days", status=status)
    data.update(extra)
    return Pilot.objects.create(**data)


def add_result(pilot, user, value="20"):
    return PilotResult.objects.create(
        pilot=pilot, value=Decimal(value), measured_on=date(2026, 12, 15),
        method_note="Timed on 5 days", recorded_by=user)


# ---------------------------------------------------------------- submit
def test_the_owner_can_submit_a_complete_draft(problem, planner):
    pilot = new_pilot(problem, planner)
    workflow.submit_for_review(pilot, planner)
    pilot.refresh_from_db()
    assert pilot.status == "review"


def test_an_incomplete_draft_cannot_be_submitted(problem, planner):
    pilot = new_pilot(problem, planner, baseline_value=None)
    with pytest.raises(ValidationError):
        workflow.submit_for_review(pilot, planner)


def test_someone_else_cannot_submit_a_pilot(problem, planner, frontline):
    pilot = new_pilot(problem, planner)
    with pytest.raises(PermissionDenied):
        workflow.submit_for_review(pilot, frontline)
    pilot.refresh_from_db()
    assert pilot.status == "draft"


# --------------------------------------------------------------- approve
def test_a_manager_can_approve_a_pilot_in_review(problem, planner, manager):
    pilot = new_pilot(problem, planner, status="review")
    workflow.approve(pilot, manager)
    pilot.refresh_from_db()
    assert pilot.status == "approved"


def test_a_planner_who_is_not_a_manager_cannot_approve(problem, planner):
    other_planner = make_user("planner2", roles.PLANNER_GROUP)
    pilot = new_pilot(problem, planner, status="review")
    with pytest.raises(PermissionDenied):
        workflow.approve(pilot, other_planner)


def test_nobody_can_approve_their_own_pilot(problem, manager):
    pilot = new_pilot(problem, manager, status="review")
    with pytest.raises(PermissionDenied):
        workflow.approve(pilot, manager)


def test_only_a_pilot_in_review_can_be_approved(problem, planner, manager):
    pilot = new_pilot(problem, planner)  # still a draft
    with pytest.raises(ValidationError):
        workflow.approve(pilot, manager)


def test_an_admin_can_approve(problem, planner):
    admin = make_user("admin1", superuser=True)
    pilot = new_pilot(problem, planner, status="review")
    workflow.approve(pilot, admin)
    pilot.refresh_from_db()
    assert pilot.status == "approved"


# ----------------------------------------------------------------- start
def test_an_approved_pilot_can_start(problem, planner):
    pilot = new_pilot(problem, planner, status="approved")
    workflow.start_pilot(pilot, planner, date(2026, 12, 1))
    pilot.refresh_from_db()
    problem.refresh_from_db()
    assert pilot.status == "running"
    assert problem.status == "in_pilot"


def test_a_pilot_that_is_not_approved_cannot_start(problem, planner):
    pilot = new_pilot(problem, planner, status="review")
    with pytest.raises(ValidationError):
        workflow.start_pilot(pilot, planner, date(2026, 12, 1))


def test_a_frontline_user_cannot_start_a_pilot(problem, planner, frontline):
    pilot = new_pilot(problem, planner, status="approved")
    with pytest.raises(PermissionDenied):
        workflow.start_pilot(pilot, frontline, date(2026, 12, 1))


# ---------------------------------------------------------------- finish
def test_finishing_needs_at_least_one_result(problem, planner):
    pilot = new_pilot(problem, planner, status="running",
                      start_date=date(2026, 12, 1))
    with pytest.raises(ValidationError):
        workflow.finish(pilot, planner, date(2026, 12, 20))


def test_finishing_a_pilot_resolves_the_problem(problem, planner):
    pilot = new_pilot(problem, planner, status="running",
                      start_date=date(2026, 12, 1))
    add_result(pilot, planner)
    workflow.finish(pilot, planner, date(2026, 12, 20))
    pilot.refresh_from_db()
    problem.refresh_from_db()
    assert pilot.status == "finished"
    assert pilot.end_date == date(2026, 12, 20)
    assert problem.status == "resolved"


def test_the_end_date_cannot_be_before_the_start_date(problem, planner):
    pilot = new_pilot(problem, planner, status="running",
                      start_date=date(2026, 12, 10))
    add_result(pilot, planner)
    with pytest.raises(ValidationError):
        workflow.finish(pilot, planner, date(2026, 12, 5))