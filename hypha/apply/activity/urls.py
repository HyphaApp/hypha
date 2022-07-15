from django.urls import include, path

from .views import NotificationsView

app_name = 'activity'


urlpatterns = [
    path('anymail/', include('anymail.urls')),
    path('notifications/', NotificationsView.as_view(), name='notifications')
]
