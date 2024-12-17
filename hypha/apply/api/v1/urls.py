from rest_framework_nested import routers

from .views import RoundViewSet

app_name = "v1"

router = routers.SimpleRouter()
router.register("rounds", RoundViewSet, basename="rounds")

urlpatterns = router.urls
