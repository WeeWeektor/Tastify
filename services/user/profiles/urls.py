from django.urls import path

from profiles.views import CustomerProfileView

urlpatterns = [
    path("me/", CustomerProfileView.as_view(), name="profile-me"),
]
