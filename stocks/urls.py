from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('buy', views.buy, name='buy'),
    path('sell', views.sell, name='sell'),
    path('history', views.history, name='history'),
    path('quote', views.quote, name='quote'),
    path("groups", views.groups, name='groups'),
    path("leave", views.leave, name="leave"),
    path("group_register", views.group_register, name='group_register'),
    path("profile", views.profile, name='profile'),
    path("graph/<str:symbol>", views.graph, name='graph')
]