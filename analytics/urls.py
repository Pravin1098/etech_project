
from django.urls import path
from .views import monthly_summaries

urlpatterns = [
    path("summaries/", monthly_summaries, name="monthly-summaries"),
]