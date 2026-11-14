"""Who may do what. Roles are Django groups; admins are superusers.

Frontline staff need no group: they can report problems and see their own.
"""
PLANNER_GROUP = "DX planner"
MANAGER_GROUP = "Manager"


def _in_group(user, name):
    return user.is_authenticated and user.groups.filter(name=name).exists()


def can_plan(user):
    """May submit pilots, start them and finish them."""
    return user.is_superuser or _in_group(user, PLANNER_GROUP)


def can_approve(user):
    """May approve a pilot that is in review."""
    return user.is_superuser or _in_group(user, MANAGER_GROUP)