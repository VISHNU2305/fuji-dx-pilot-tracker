from django.urls import path

from . import views

urlpatterns = [
    path("", views.problem_list, name="problem_list"),
    path("problems/new/", views.problem_create, name="problem_create"),
]