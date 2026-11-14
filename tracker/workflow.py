"""The pilot approval flow: draft -> review -> approved -> running -> finished.

Every function checks the actor's role and the pilot's current status on the
server, so a change to a web address cannot skip a step.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from . import roles
from .models import Pilot, Problem


def _require_status(pilot, expected, action):
    if pilot.status != expected:
        raise ValidationError(
            f"Cannot {action}: the pilot is '{pilot.get_status_display()}', "
            f"not '{Pilot.Status(expected).label}'.")


def submit_for_review(pilot, actor):
    if not (actor == pilot.owner or roles.can_plan(actor)):
        raise PermissionDenied("Only the owner or a DX planner can submit a pilot.")
    _require_status(pilot, Pilot.Status.DRAFT, "submit")
    missing = pilot.missing_for_start()
    if missing:
        raise ValidationError(
            "Before review the pilot needs " + ", ".join(missing) + ".")
    pilot.status = Pilot.Status.REVIEW
    pilot.save(update_fields=["status"])


def approve(pilot, actor):
    if not roles.can_approve(actor):
        raise PermissionDenied("Only a manager can approve a pilot.")
    if actor == pilot.owner:
        raise PermissionDenied("You cannot approve your own pilot.")
    _require_status(pilot, Pilot.Status.REVIEW, "approve")
    pilot.status = Pilot.Status.APPROVED
    pilot.save(update_fields=["status"])


def start_pilot(pilot, actor, on):
    if not roles.can_plan(actor):
        raise PermissionDenied("Only a DX planner can start a pilot.")
    _require_status(pilot, Pilot.Status.APPROVED, "start")
    pilot.start(on)  # also enforces the metric and baseline rule


def finish(pilot, actor, on):
    if not roles.can_plan(actor):
        raise PermissionDenied("Only a DX planner can finish a pilot.")
    _require_status(pilot, Pilot.Status.RUNNING, "finish")
    if not pilot.results.exists():
        raise ValidationError("Record at least one result before finishing.")
    if pilot.start_date and on < pilot.start_date:
        raise ValidationError("The end date cannot be before the start date.")
    with transaction.atomic():
        pilot.status = Pilot.Status.FINISHED
        pilot.end_date = on
        pilot.save(update_fields=["status", "end_date"])
        pilot.problem.status = Problem.Status.RESOLVED
        pilot.problem.save(update_fields=["status"])