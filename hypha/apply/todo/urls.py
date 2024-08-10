from django.urls import path

from .views import TaskRemovalView, TodoListView

app_name = "hypha.apply.todo"


urlpatterns = [
    path("todo/list/", TodoListView.as_view(), name="list"),
    path("todo/<int:pk>/delete/", TaskRemovalView.as_view(), name="delete"),
]
