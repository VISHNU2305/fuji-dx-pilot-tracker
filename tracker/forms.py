from django import forms

from .models import Problem


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ["business", "title", "description", "workflow",
                  "times_per_month", "minutes_per_time", "people_affected"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "workflow": forms.Textarea(attrs={"rows": 4}),
        }