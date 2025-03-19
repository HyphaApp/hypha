from django.shortcuts import render

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
