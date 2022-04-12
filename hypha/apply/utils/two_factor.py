from django.shortcuts import get_object_or_404

from .models import TWOFASettings


def check_two_factor_settings(site):
    two_fa_settings = get_object_or_404(TWOFASettings, site=site)
    return two_fa_settings.two_factor_required
