from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProblemForm
from .models import Problem


@login_required
def problem_list(request):
    """Staff see every problem. Everyone else sees only their own reports."""
    problems = Problem.objects.select_related("business", "reported_by")
    if not request.user.is_staff:
        problems = problems.filter(reported_by=request.user)
    return render(request, "tracker/problem_list.html",
                  {"problems": problems.order_by("-created_at")})


@login_required
def problem_create(request):
    if request.method == "POST":
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            problem.reported_by = request.user
            problem.save()
            return redirect("problem_list")
    else:
        form = ProblemForm()
    return render(request, "tracker/problem_form.html", {"form": form})