from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('contract_requests', views.contract_requests_list, name='contract_requests_list'),
    path('speakers', views.speakers, name='speakers'),
    path('speakers/<int:speaker_id>/details', views.speaker_details, name='speaker_details')
]
