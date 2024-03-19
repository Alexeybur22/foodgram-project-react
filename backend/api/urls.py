from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TokenObtainViewSet, UserViewSet



router_version1 = DefaultRouter()
router_version1.register(
    'users',
    UserViewSet,
    basename='user'
)


token_urls = [
    path('login/', TokenObtainViewSet.as_view(), name='token_obtain'),
#    path('logout/', TokenObtainViewSet.as_view(), name='token_obtain'),
]

urlpatterns = [
    path('', include(router_version1.urls)),
    path('auth/token/', include(token_urls))
]