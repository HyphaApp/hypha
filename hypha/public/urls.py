from django.urls import path

from .partner import views as partner_views

urlpatterns = [
    path(
        "about/portfolio/",
        partner_views.InvestmentTableView.as_view(),
        name="investments",
    ),
]
