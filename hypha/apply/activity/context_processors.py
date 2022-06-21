from .models import Activity


def notification_context(request):
    context_data = dict()
    if request.user.is_authenticated:
        context_data['latest_notifications'] = Activity.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return context_data
