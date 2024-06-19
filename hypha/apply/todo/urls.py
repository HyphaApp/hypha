from django.urls import path

from .views import TodoListView

app_name = "hypha.apply.todo"


urlpatterns = [
    path("todo/list/", TodoListView.as_view(), name="list"),
]
