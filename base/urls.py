from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),  # Root URL redirects to login
    path('login/', views.login_view, name='login'),  # Keep this for explicit login URL
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # try:
    #     import debug_toolbar
    #     urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    # except ImportError:
    #     pass