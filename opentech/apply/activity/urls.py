from django.urls import include, path


app_name = 'activity'


urlpatterns = [
    path('anymail/', include('anymail.urls')),
]
