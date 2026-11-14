"""How the effect of a pilot is calculated.

hours saved per month = (minutes before - minutes after) x times per month / 60
improvement (%)       = (before - after) / before x 100

Both are rounded to one decimal place.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

ONE_DECIMAL = Decimal("0.1")


def _round1(value):
    return value.quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)


def hours_saved_per_month(minutes_before, minutes_after, times_per_month):
    before, after = Decimal(minutes_before), Decimal(minutes_after)
    return _round1((before - after) * Decimal(times_per_month) / Decimal(60))


def improvement_percent(before, after):
    before = Decimal(before)
    if before == 0:
        raise ValueError("The baseline is zero, so a percentage cannot be calculated.")
    return _round1((before - Decimal(after)) / before * Decimal(100))


def pilot_effect(pilot):
    """The effect of a pilot, from its baseline and its latest recorded result."""
    if pilot.unit != "minutes":
        raise ValidationError(
            "Hours saved can only be calculated for a metric measured in minutes.")
    if pilot.baseline_value is None:
        raise ValidationError("The pilot has no baseline.")
    result = pilot.results.order_by("-measured_on", "-id").first()
    if result is None:
        raise ValidationError("No result has been recorded yet.")
    return {
        "baseline": pilot.baseline_value,
        "result": result.value,
        "measured_on": result.measured_on,
        "method": result.method_note,
        "hours_saved_per_month": hours_saved_per_month(
            pilot.baseline_value, result.value, pilot.problem.times_per_month),
        "improvement_percent": improvement_percent(
            pilot.baseline_value, result.value),
    }