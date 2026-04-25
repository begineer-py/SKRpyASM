from ninja import NinjaAPI
from django.urls import path

api = NinjaAPI()
urlpatterns = [
    path("api/", api.urls),
]
