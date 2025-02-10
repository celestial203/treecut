from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Root URL redirects to login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cutting/', views.cutting, name='cutting'),
    path('wood/', views.wood, name='wood'),
    path('lumber/', views.lumber, name='lumber'),
    path('edit_recordlumber/<int:pk>/', views.edit_recordlumber, name='edit_recordlumber'),
    path('search/', views.search, name='search'),
    path('chainsaw/', views.chainsaw, name='chainsaw'),
    path('edit-chainsaw/<str:pk>/', views.edit_chainsaw, name='edit_chainsaw'),
    path('edit-wood/<int:pk>/', views.edit_wood, name='edit_wood'),
    path('profile/', views.profile, name='profile'),
]