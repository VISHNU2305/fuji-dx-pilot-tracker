import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Business, Problem

pytestmark = pytest.mark.django_db


@pytest.fixture
def hotel():
    return Business.objects.create(name="Hotels")


def make_user(name, staff=False):
    return User.objects.create_user(name, password="pw-12345-test", is_staff=staff)


def valid_data(hotel, **extra):
    data = {"business": hotel.id, "title": "Daily report is slow",
            "description": "Report takes too long", "workflow": "Export, copy, paste",
            "times_per_month": 22, "minutes_per_time": 60, "people_affected": 2}
    data.update(extra)
    return data


def test_hours_lost_per_month_is_calculated(hotel):
    p = Problem(business=hotel, times_per_month=22, minutes_per_time=60)
    assert p.hours_lost_per_month == 22  # 22 times x 60 minutes / 60


def test_reporting_requires_login(client):
    response = client.get(reverse("problem_create"))
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


def test_logged_in_user_can_report_a_problem(client, hotel):
    user = make_user("frontline1")
    client.force_login(user)
    response = client.post(reverse("problem_create"), valid_data(hotel))
    assert response.status_code == 302
    assert Problem.objects.get().reported_by == user


def test_zero_minutes_is_refused(client, hotel):
    client.force_login(make_user("frontline1"))
    response = client.post(reverse("problem_create"),
                           valid_data(hotel, minutes_per_time=0))
    assert response.status_code == 200
    assert Problem.objects.count() == 0


def test_a_user_sees_only_their_own_problems(client, hotel):
    a, b = make_user("user_a"), make_user("user_b")
    client.force_login(a)
    client.post(reverse("problem_create"), valid_data(hotel, title="Problem from A"))
    client.force_login(b)
    response = client.get(reverse("problem_list"))
    assert b"Problem from A" not in response.content


def test_staff_see_every_problem(client, hotel):
    client.force_login(make_user("user_a"))
    client.post(reverse("problem_create"), valid_data(hotel, title="Problem from A"))
    client.force_login(make_user("planner", staff=True))
    response = client.get(reverse("problem_list"))
    assert b"Problem from A" in response.content