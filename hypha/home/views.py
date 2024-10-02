from django.shortcuts import render

from hypha.apply.funds.models import ApplicationBase, LabBase


def home(request):
    """Home page view.

    Displays the list of active rounds and labs to both logged in and logged out users.
    """
    ctx = {}
    rounds = ApplicationBase.objects.order_by_end_date().specific()
    labs = LabBase.objects.public().live().specific()

    ctx["funds"] = list(rounds) + list(labs)
    return render(request, "home/home.html", ctx)
