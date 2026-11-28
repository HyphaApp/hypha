from django.shortcuts import render

from hypha.apply.funds.models import ApplicationBase, LabBase, RoundBase


def home(request):
    """Home page view.

    Displays the list of active rounds and labs to both logged in and logged out users.
    """
    ctx = {}
    rounds = (
        ApplicationBase.objects.order_by_end_date()
        .filter(list_on_front_page=True)
        .specific()
    )
    labs = LabBase.objects.public().live().filter(list_on_front_page=True).specific()

    # Fetch all open rounds in one query and attach each to its parent fund.
    #
    # Wagtail pages store their tree position as a materialised path made of
    # fixed-width steps, one per level (steplen = 4), e.g.
    #   000100020005      a fund
    #   0001000200050003  a round under that fund
    # Removing the last step from a round's path gives its parent fund's path.
    #
    # A fund should only have one open round, but if it has several,
    # setdefault() keeps the first round stored for each fund and ignores
    # later ones. Ordering by path makes that the same round the fund page
    # serves, ApplicationBase.open_round (child_of(fund).open().first()).
    open_rounds = {}
    for open_round in RoundBase.objects.open().order_by("path"):
        open_rounds.setdefault(open_round.path[: -RoundBase.steplen], open_round)

    funds = []
    for fund in rounds:
        fund.open_round = open_rounds.get(fund.path)
        if fund.open_round:
            funds.append(fund)

    # Only pass rounds/labs that are open & visible for the front page
    ctx["funds"] = funds + list(labs)
    return render(request, "home/home.html", ctx)
