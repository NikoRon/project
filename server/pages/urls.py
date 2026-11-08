from django.urls import path

from .views import auditView, balanceView, homePageView, searchView, transferView

urlpatterns = [
    path('', homePageView, name='home'),
    path('balance/', balanceView, name='balance'),
    path('transfer/', transferView, name='transfer'),
    path('search/', searchView, name='search'),
    path('audit/', auditView, name='audit'),
]
