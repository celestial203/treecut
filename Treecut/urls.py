# Treecut/urls.py

from django.contrib import admin
from django.urls import path, include
from base import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),  # Include the base app URLs
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cutting/', views.cutting, name='cutting'),
   path('cutting/edit/<int:pk>/', views.edit_cutting, name='edit_cutting'),
    path('lumber/', views.lumber, name='lumber'),
    path('chainsaw/', views.chainsaw, name='chainsaw'),
    path('wood/', views.wood, name='wood'),
    path('search/', views.search, name='search'),
    path('profile/', views.profile, name='profile'),
]

# Add this conditional for serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
