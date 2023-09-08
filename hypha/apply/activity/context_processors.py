from .models import Activity


def notification_context(request):
    context_data = {}
    if hasattr(request, "user"):
        if request.user.is_authenticated and request.user.is_apply_staff:
            context_data["latest_notifications"] = (
                Activity.objects.filter(current=True)
                .latest()
                .order_by("-timestamp")[:5]
            )
    return context_data
