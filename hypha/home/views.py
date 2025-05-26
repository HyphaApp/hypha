from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from hypha.apply.funds.models import ApplicationBase, LabBase


def home(request):
    """Home page view.

    Displays the list of active rounds and labs to both logged in and logged out users.
    """
    ctx = {}
    rounds = ApplicationBase.objects.order_by_end_date().specific()
    labs = LabBase.objects.public().live().specific()
    all_funds = list(rounds) + list(labs)

    # Only pass rounds/labs that are open & visible for the front page
    ctx["funds"] = [
        fund for fund in all_funds if fund.open_round and fund.list_on_front_page
    ]
    return render(request, "home/home.html", ctx)


@ratelimit(key="ip", rate=settings.DEFAULT_RATE_LIMIT)
def open_calls_json(request):
    """Open calls in JSON format.

    List open calls in JSON format, useful when you want to list open calls on an external site.
    """
    rounds = ApplicationBase.objects.order_by_end_date().specific()
    labs = LabBase.objects.public().live().specific()
    all_funds = list(rounds) + list(labs)

    # Only pass rounds/labs that are open & visible for the front page
    data = [
        fund.as_json
        for fund in all_funds
        if fund.open_round and fund.list_on_front_page
    ]
    return JsonResponse(data, safe=False)
